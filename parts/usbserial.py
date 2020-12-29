# -*- coding: utf-8 -*-

import serial
import numpy as np
import math


def _uchar_checksum(data):
    length = len(data)
    checksum = 0
    for i in range(0, length):
        checksum += data[i]
    # 强制截断
    checksum &= 0xFF
    return checksum


def _get_2_hex(dec):
    if dec >= 0:
        return 0X00, dec % 0xFF
    else:
        return 0XFF, dec % 256


class CarEngine:
    LEFT_ANGLE = -1.0
    RIGHT_ANGLE = 1.0
    left_pulse = -100
    right_pulse = 100

    def __init__(self, dev='/dev/ttyUSB0'):
        self.port = serial.Serial(dev, 115200, timeout=1)

    def run(self, angle, throttle):
        # map absolute angle to angle that vehicle can implement.
        if abs(angle) < 1e-4 and abs(throttle) < 1e-4:
            return
        else:
            raw_pulse = np.ones(4)
            filter = np.array([[1, -1, 1, -1], [1, -1, 1, -1], [1, -1, 1, -1], [1, -1, 1, -1]])
            filter_pulse = np.dot(raw_pulse, filter * 0.25) * math.exp(angle-1) * math.exp(throtlle-1)
            print("angle and throttle is", angle, throttle, "input pulse is", filter_pulse)
            self._move(filter_pulse[0], filter_pulse[1], filter_pulse[2], filter_pulse[3])

    def _move(self, left_forward, right_forward, left_back, right_back):
        left_forward_pulse = self._map_range(left_forward)
        first_left_forward, second_left_forward = _get_2_hex(left_forward_pulse)

        right_forward_pulse = self._map_range(right_forward)
        first_right_forward, second_right_forward = _get_2_hex(right_forward_pulse)

        left_back_pulse = self._map_range(left_back)
        first_left_back, second_left_back = _get_2_hex(left_back_pulse)

        right_back_pulse = self._map_range(right_back)
        first_right_back, second_right_back = _get_2_hex(right_back_pulse)

        my_input = [0xFE, 0XEF, 0X08, first_left_forward, second_left_forward,
                    first_right_forward, second_right_forward, first_left_back, second_left_back,
                    first_right_back, second_right_back]  # 需要发送的十六进制数据
        sum_check = _uchar_checksum(my_input)
        my_input.append(sum_check)
        self.port.write(my_input)  # 用write函数向串口发送数据

    def _map_range(self, x):
        """
        Linear mapping between two ranges of values
        """
        x_range = self.RIGHT_ANGLE - self.LEFT_ANGLE
        y_range = self.right_pulse - self.left_pulse
        xy_ratio = x_range * 1.0 / y_range

        y = ((x - self.LEFT_ANGLE) / xy_ratio + self.left_pulse) // 1
        return int(y)

    def shutdown(self):
        self.port.close()


if __name__ == '__main__':
    engine = CarEngine(dev='/dev/cu.usbserial-14210')
    engine._move(0.2, -0.2, 0.2, -0.2)
    # engine.move(0.1, 0, 0, 0)
    engine.shutdown()
