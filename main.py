#!/usr/bin/env python3
"""
Scripts to drive a donkey 2 car and train a model for it.

Usage:
    manage.py (drive) [--model=<model>] [--js] [--chaos]
    manage.py (train) [--tub=<tub1,tub2,..tubn>]  (--model=<model>) [--base_model=<base_model>] [--no_cache]

Options:
    -h --help        Show this screen.
    --tub TUBPATHS   List of paths to tubs. Comma separated. Use quotes to use wildcards. ie "~/tubs/*"
    --chaos          Add periodic random steering when manually driving
"""
import os

from docopt import docopt
from parts.camera import PiCamera
from parts.clock import Timestamp
from parts.datastore import Tub, TubWriter
from vehicle import Vehicle


class Config:
    def __init__(self):
        pass

    def from_pyfile(self, filename, silent=False):
        """
        Read config class from a file.
        """
        d = types.ModuleType('config')
        d.__file__ = filename
        try:
            with open(filename, mode='rb') as config_file:
                exec (compile(config_file.read(), filename, 'exec'), d.__dict__)
        except IOError as e:
            e.strerror = 'Unable to load configuration file (%s)' % e.strerror
            raise
        self.from_object(d)
        return True

    def from_object(self, obj):
        """
        Read config class from another object.
        """
        for key in dir(obj):
            if key.isupper():
                setattr(self, key, getattr(obj, key))

    def __str__(self):
        """
        Get a string representation of the config class.
        """
        result = []
        for key in dir(self):
            if key.isupper():
                result.append((key, getattr(self, key)))
        return str(result)


def load_config(config_path=None):
    """
    Load the config from a file and return the config class.
    """
    if config_path is None:
        import __main__ as main
        main_path = os.path.dirname(os.path.realpath(main.__file__))
        config_path = os.path.join(main_path, 'config_defaults.py')

    print('loading config file: {}'.format(config_path))
    cfg = Config()
    cfg.from_pyfile(config_path)
    print('config loaded')
    return cfg


def drive(config):
    V = Vehicle()
    clock = Timestamp()
    V.add(clock, outputs=['timestamp'])

    cam = PiCamera(resolution=config.CAMERA_RESOLUTION)
    V.add(cam, outputs=['image'], threaded=True)

    tub = TubWriter(path='~/mycar',
                    inputs=['image'],
                    types=['image_array'])
    V.add(tub, inputs=['image'])
    # run the vehicle
    V.start(rate_hz=config.DRIVE_LOOP_HZ,
            max_loop_count=config.MAX_LOOPS)


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = load_config()

    if args['drive']:
        drive(cfg)
