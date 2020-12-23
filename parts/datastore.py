#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  4 12:32:53 2017

@author: wroscoe
"""
import os
import sys
import time
import json
import datetime
import random
import tarfile

import numpy as np
import pandas as pd
from PIL import Image

from ..log import get_logger

logger = get_logger(__name__)


class Tub(object):
    """
    A datastore to store sensor data in a key, value format.

    Accepts str, int, float, image_array, image, and array data types.

    For example:

    #Create a tub to store speed values.
    >>> path = '~/mycar/test_tub'
    >>> inputs = ['user/speed', 'cam/image']
    >>> types = ['float', 'image']
    >>> t=Tub(path=path, inputs=inputs, types=types)

    """

    def __init__(self, path, inputs=None, types=None):

        self.path = os.path.expanduser(path)
        logger.info('path_in_tub: {}'.format(self.path))
        self.meta_path = os.path.join(self.path, 'meta.json')
        self.df = None

        exists = os.path.exists(self.path)
        if exists:
            # load log and meta
            logger.info('Tub exists: {}'.format(self.path))
            with open(self.meta_path, 'r') as f:
                self.meta = json.load(f)
            self.current_ix = self.get_last_ix() + 1

        elif not exists and inputs:
            logger.info('Tub does NOT exist. Creating new tub...')
            # create log and save meta
            os.makedirs(self.path)
            self.meta = {'inputs': inputs, 'types': types}
            with open(self.meta_path, 'w') as f:
                json.dump(self.meta, f)
            self.current_ix = 0
            logger.info('New tub created at: {}'.format(self.path))
        else:
            msg = "The tub path you provided doesn't exist and you didnt pass any meta info (inputs & types)" + \
                  "to create a new tub. Please check your tub path or provide meta info to create a new tub."

            raise AttributeError(msg)

        self.start_time = time.time()

    def get_last_ix(self):
        index = self.get_index()
        if len(index) >= 1:
            return max(index)
        return -1

    def update_df(self):
        df = pd.DataFrame([self.get_json_record(i) for i in self.get_index(shuffled=False)])
        self.df = df

    def get_df(self):
        if self.df is None:
            self.update_df()
        return self.df

    def get_index(self, shuffled=True):
        files = next(os.walk(self.path))[2]
        record_files = [f for f in files if f[:6] == 'record']

        def get_file_ix(file_name):
            try:
                name = file_name.split('.')[0]
                num = int(name.split('_')[1])
            except:
                num = 0
            return num

        nums = [get_file_ix(f) for f in record_files]

        if shuffled:
            random.shuffle(nums)
        else:
            nums = sorted(nums)

        return nums

    @property
    def inputs(self):
        return list(self.meta['inputs'])

    @property
    def types(self):
        return list(self.meta['types'])

    def get_input_type(self, key):
        input_types = dict(zip(self.inputs, self.types))
        return input_types.get(key)

    def write_json_record(self, json_data):
        path = self.get_json_record_path(self.current_ix)
        try:
            with open(path, 'w') as fp:
                json.dump(json_data, fp)
        except TypeError:
            logger.warn('troubles with record: {}'.format(json_data))
        except FileNotFoundError:
            raise
        except:
            logger.error('Unexpected error: {}'.format(sys.exc_info()[0]))
            raise

    def get_num_records(self):
        import glob
        files = glob.glob(os.path.join(self.path, 'record_*.json'))
        return len(files)

    def make_record_paths_absolute(self, record_dict):
        d = {}
        for k, v in record_dict.items():
            if type(v) == str:  # filename
                if '.' in v:
                    v = os.path.join(self.path, v)
            d[k] = v

        return d

    def check(self, fix=False):
        """
        Iterate over all records and make sure we can load them.
        Optionally remove records that cause a problem.
        """
        logger.info('Checking tub: {}'.format(self.path))
        logger.info('Found: {} records'.format(self.get_num_records()))
        problems = False
        for ix in self.get_index(shuffled=False):
            try:
                self.get_record(ix)
            except:
                problems = True
                if fix is False:
                    logger.warning('problems with record {} : {}'.format(ix, self.path))
                else:
                    logger.warning('problems with record {}, removing: {}'.format(ix, self.path))
                    self.remove_record(ix)
        if not problems:
            logger.info('No problems found.')

    def remove_record(self, ix):
        """
        remove data associate with a record
        """
        record = self.get_json_record_path(ix)
        os.unlink(record)

    def put_record(self, data):
        """
        Save values like images that can't be saved in the csv log and
        return a record with references to the saved values that can
        be saved in a csv.
        """
        json_data = {}

        for key, val in data.items():
            typ = self.get_input_type(key)

            if typ in ['str', 'float', 'int', 'boolean']:
                json_data[key] = val

            elif typ is 'image':
                name = self.make_file_name(key, ext='.jpg')
                val.save(os.path.join(self.path, name))
                json_data[key] = name

            elif typ == 'image_array':
                img = Image.fromarray(np.uint8(val))
                name = self.make_file_name(key, ext='.jpg')
                img.save(os.path.join(self.path, name))
                json_data[key] = name

            else:
                msg = 'Tub does not know what to do with this type {}'.format(typ)
                raise TypeError(msg)

        self.write_json_record(json_data)
        self.current_ix += 1
        return self.current_ix

    def get_json_record_path(self, ix):
        # fill zeros
        # return os.path.join(self.path, 'record_'+str(ix).zfill(6)+'.json')
        # don't fill zeros
        return os.path.join(self.path, 'record_' + str(ix) + '.json')

    def get_json_record(self, ix):
        path = self.get_json_record_path(ix)
        try:
            with open(path, 'r') as fp:
                json_data = json.load(fp)
        except UnicodeDecodeError:
            raise Exception('bad record: %d. You may want to run `python manage.py check --fix`' % ix)
        except FileNotFoundError:
            raise
        except:
            logger.error('Unexpected error: {}'.format(sys.exc_info()[0]))
            raise

        record_dict = self.make_record_paths_absolute(json_data)
        return record_dict

    def get_record(self, ix):
        json_data = self.get_json_record(ix)
        data = self.read_record(json_data)
        return data

    def read_record(self, record_dict):
        data = {}
        for key, val in record_dict.items():
            typ = self.get_input_type(key)

            # load objects that were saved as separate files
            if typ == 'image_array':
                img = Image.open((val))
                val = np.array(img)

            data[key] = val
        return data

    def make_file_name(self, key, ext='.png'):
        # name = '_'.join([str(self.current_ix).zfill(6), key, ext])
        name = '_'.join([str(self.current_ix), key, ext])  # don't fill zeros
        name = name = name.replace('/', '-')
        return name

    def delete(self):
        """ Delete the folder and files for this tub. """
        import shutil
        shutil.rmtree(self.path)

    def shutdown(self):
        """ Required by the Part interface """
        pass

    def get_record_gen(self, record_transform=None, shuffle=True, df=None):
        """
        Returns records.

        Parameters
        ----------
        record_transform : function
            The mapping function should handle records in dict format
        shuffle : bool
            Shuffle records
        df : numpy Dataframe
            If df is specified, the generator will use the records specified in that DataFrame. If None,
            the internal DataFrame will be used by calling get_df()

        Returns
        -------
        A dict with keys mapping to the specified keys, and values lists of size batch_size.

        See Also
        --------
        get_df
        """
        if df is None:
            df = self.get_df()

        while True:
            for _ in self.df.iterrows():
                if shuffle:
                    record_dict = df.sample(n=1).to_dict(orient='record')[0]

                record_dict = self.read_record(record_dict)

                if record_transform:
                    record_dict = record_transform(record_dict)

                yield record_dict

    def get_batch_gen(self, keys=None, batch_size=128, record_transform=None, shuffle=True, df=None):
        """
        Returns batches of records.

        Additionally, each record in a batch is split up into a dict with inputs:list of values. By specifying keys as a subset of the inputs, you can filter out unnecessary data.

        Parameters
        ----------
        keys : list of strings
            List of keys to filter out. If None, all inputs are included.
        batch_size : int
            The number of records in one batch.

        Returns
        -------
        A dict with keys mapping to the specified keys, and values lists of size batch_size.

        See Also
        --------
        get_record_gen
        """
        record_gen = self.get_record_gen(record_transform=record_transform, shuffle=shuffle, df=df)

        if df is None:
            df = self.get_df()

        if keys is None:
            keys = list(self.df.columns)

        while True:
            record_list = [ next(record_gen) for _ in range(batch_size) ]
            batch_arrays = {}
            for i, k in enumerate(keys):
                arr = np.array([r[k] for r in record_list])
                batch_arrays[k] = arr
            yield batch_arrays

    def tar_records(self, file_path, start_ix=None, end_ix=None):
        """
        Create a tarfile of the records and metadata from a tub.

        Compress using gzip.

        Parameters
        ----------
        file_path : string
            The destination path of the created tar archive
        start_ix : int
            Start index. Defaults to 0.
        end_ix : int
            End index. Defaults to last index.

        Returns
        -------
        Path to the tar archive
        """
        if not start_ix:
            start_ix = 0

        if not end_ix:
            end_ix = self.get_last_ix() + 1

        with tarfile.open(name=file_path, mode='w:gz') as f:
            for ix in range(start_ix, end_ix):
                record_path = self.get_json_record_path(ix)
                f.add(record_path)
            f.add(self.meta_path)

        return file_path


class TubWriter(Tub):
    def __init__(self, *args, **kwargs):
        super(TubWriter, self).__init__(*args, **kwargs)

    def run(self, *args):
        """
        Accepts values, pairs them with their input keys and saves them
        to disk.
        """
        assert len(self.inputs) == len(args)
        record = dict(zip(self.inputs, args))
        self.put_record(record)