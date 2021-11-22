from minio import Minio
from minio.error import InvalidResponseError
import os
from log import get_logger

logger = get_logger(__name__)


class UpAndDownload(object):
    def __init__(self, path,endpoint, access_key, secret_key):
        self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False, )
        self.path = os.path.expanduser(path)

    def get_dir_base_on_prefix(self, path, prefix):
        dirs = os.listdir(os.path.expanduser(path))
        targetDir = []
        for dir in dirs:
            if dir[:len(prefix)] == prefix:
                targetDir.append(dir)
        return targetDir

    def upload_data(self):
        targetDir = self.get_dir_base_on_prefix(self.path, prefix="tub")
        for bucket in targetDir:
            location = "use-east-1"
            result = os.listdir(os.path.join(self.path, bucket))
            if len(result) < 1000:
                continue
            new_bucket_name = bucket.replace('_', '-')
            exist = self.client.bucket_exists(bucket_name=new_bucket_name)

            if exist:
                # print('bucket {} has already been.'.format(new_bucket_name))
                logger.info('Bucket {} has already been.'.format(bucket))
            else:
                self.client.make_bucket(bucket_name=new_bucket_name)
                logger.info("Bucket {} Successfully created ".format(bucket))
                # print('bucket {} successfully create has already been.'.format(new_bucket_name))
                targetObjects = self.get_dir_base_on_prefix(os.path.join(self.path, bucket), "")
                for object_name in targetObjects:
                    object_path = os.path.join(self.path, bucket, object_name)
                    self.client.fput_object(bucket_name=new_bucket_name, object_name=object_name, file_path=object_path)

    def download_data(self,bucket_name,object_name):
        exist = self.client.bucket_exists(bucket_name)
        if exist :
            self.client.fget_object(bucket_name,object_name,os.path.join(self.path,bucket_name,object_name))
            logger.info("Object {} has downloaded successfully".format(object_name))
        else :
            logger.error("Bucket {} does not exist".format(bucket_name))


    def delete_bucket(self, bucket_name):
        objectlist = self.client.list_objects(bucket_name=bucket_name)
        for one_object in objectlist:
            self.client.remove_object(bucket_name=bucket_name, object_name=one_object.object_name)
        self.client.remove_bucket(bucket_name=bucket_name)



if __name__ == "__main__":
    up = Updata(path="~/mycar")
    up.upload_data()
