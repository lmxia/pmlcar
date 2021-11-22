"""
CAR CONFIG

This file is read by your car application's manage.py script to change the car
performance.

EXMAPLE
-----------
import dk
cfg = dk.load_config(config_path='~/mycar/config.py')
print(cfg.CAMERA_RESOLUTION)

"""

import os

# PATHS
CAR_PATH = PACKAGE_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = "~/mycar"
MODELS_PATH = "~/mycar/model"

# VEHICLE
DRIVE_LOOP_HZ = 20
MAX_LOOPS = 100000

# CAMERA
CAMERA_RESOLUTION = (120, 160)  # (height, width)
CAMERA_FRAMERATE = DRIVE_LOOP_HZ

# TRAINING
BATCH_SIZE = 128
TRAIN_TEST_SPLIT = 0.8

#CLOUD
CLOUD_IP = "106.12.88.113"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
