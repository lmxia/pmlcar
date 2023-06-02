#!/usr/bin/env python3

import os
from config import load_config
from parts.camera import PiCamera
from parts.clock import Timestamp
from parts.datastore import TubHandler
from parts.keras import KerasLinear
from parts.transform import Lambda
from parts.usbserial import CarEngine
from vehicle import Vehicle
from parts.web_controller import LocalWebController


def drive(config):
    V = Vehicle()
    clock = Timestamp()
    V.add(clock, outputs=['timestamp'])

    cam = PiCamera(resolution=config.CAMERA_RESOLUTION)
    V.add(cam, outputs=['cam/image_array'], threaded=True)

    # See if we should even run the pilot module
    # This is only needed because the part run condition only accepts boolean
    def pilot_condition(mode):
        if mode == 'user':
            return False
        else:
            return True

    pilot_condition_part = Lambda(pilot_condition)  # 是否开启多线程，如果为自动，run_pilot=true
    V.add(pilot_condition_part, inputs=['user/mode'], outputs=['run_pilot'])

    # Run the pilot if the mode is not user
    kl = KerasLinear()
    model_path = config.MODELS_PATH
    model_path = os.path.expanduser(model_path)
    if os.path.exists(model_path):
        kl.load(model_path)

    V.add(kl, inputs=['cam/image_array'],
          outputs=['pilot/angle', 'pilot/throttle'],
          run_condition='run_pilot')

    ctr = LocalWebController(kl)
    V.add(ctr,
          inputs=['cam/image_array'],
          outputs=['user/angle', 'user/throttle', 'user/mode', 'recording'],
          threaded=True)



    # Choose what inputs should change the car
    def drive_mode(mode,
                   user_angle, user_throttle,
                   pilot_angle, pilot_throttle):
        if mode == 'user':
            return user_angle, user_throttle
        else:
            return pilot_angle, pilot_throttle

    drive_mode_part = Lambda(drive_mode)
    V.add(drive_mode_part, inputs=['user/mode', 'user/angle', 'user/throttle',
                                   'pilot/angle', 'pilot/throttle'],
          outputs=['angle', 'throttle'])

    engine = CarEngine()
    V.add(engine, inputs=['angle', 'throttle'])

    # add tub to save data
    inputs = ['cam/image_array', 'user/angle', 'user/throttle', 'user/mode']
    types = ['image_array', 'float', 'float', 'str']

    tub_path = cfg.DATA_PATH
    tub_path = os.path.expanduser(tub_path)
    if not os.path.exists(tub_path):
        os.mkdir(tub_path)

    th = TubHandler(path=tub_path)
    tub = th.new_tub_writer(inputs=inputs, types=types)

    V.add(tub, inputs=inputs, run_condition='recording')

    # run the vehicle
    V.start(rate_hz=config.DRIVE_LOOP_HZ,
            max_loop_count=config.MAX_LOOPS)


if __name__ == '__main__':
    cfg = load_config()
    drive(cfg)
