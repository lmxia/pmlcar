#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun 24 20:10:44 2017

@author: wroscoe

remotes.py

The client and web server needed to control a car remotely.
"""
import time
import subprocess
from tornado.options import define, options, parse_command_line
import random
import tempfile
import tarfile
import boto3
import threading
import sys
import os
import os.path
import time
import sagemaker as sage
import pyinotify
from time import gmtime,strftime
from sagemaker import get_execution_role
import tornado.websocket
import tornado.httpserver
import tornado
import tornado.ioloop
import tornado.web
import tornado.gen
import shutil
import json
from threading import Thread
from tornado.ioloop import IOLoop
import socket


class LocalWebController(tornado.web.Application):
    port = 8887

    def __init__(self):
        """
        Create and publish variables needed on many of
        the web handlers.
        """
        print('Starting Car Server...')
        
        this_dir = os.path.dirname(os.path.realpath(__file__))
        self.static_file_path = os.path.join(this_dir, 'templates', 'static')

        self.angle = 0.0
        self.throttle = 0.0
        self.mode = 'user'
        self.recording = False

        self.chaos_on = False
        self.chaos_counter = 0
        self.chaos_frequency = 1000  # frames
        self.chaos_duration = 10

        handlers = [
            (r"/", tornado.web.RedirectHandler, dict(url="/drive")),
            (r"/drive", DriveAPI),
            (r"/video", VideoAPI),
            (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": self.static_file_path}),
        ]

        settings = {'debug': True}
        super().__init__(handlers, **settings)

    def update(self):
        """ Start the tornado web server. """
        self.port = int(self.port)
        self.listen(self.port)
        instance = tornado.ioloop.IOLoop.instance()
        instance.add_callback(self.say_hello)
        instance.start()

    def run_threaded(self, img_arr=None):
        self.img_arr = img_arr


    def shutdown(self):
        pass


class DriveAPI(tornado.web.RequestHandler):
    def get(self):
        data = {}
        self.render("templates/vehicle.html", **data)

    def post(self):
        """
        Receive post requests as user changes the angle
        and throttle of the vehicle on a the index webpage
        """
        data = tornado.escape.json_decode(self.request.body)
        self.application.angle = data['angle']
        self.application.throttle = data['throttle']
        self.application.mode = data['drive_mode']
        self.application.recording = data['recording']


class VideoAPI(tornado.web.RequestHandler):
    """
    Serves a MJPEG of the images posted from the vehicle.
    """

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):

        ioloop = tornado.ioloop.IOLoop.current()
        self.set_header("Content-type", "multipart/x-mixed-replace;boundary=--boundarydonotcross")

        self.served_image_timestamp = time.time()
        my_boundary = "--boundarydonotcross"
        while True:

            interval = .1
            if self.served_image_timestamp + interval < time.time():

                img = util.img.arr_to_binary(self.application.img_arr)

                self.write(my_boundary)
                self.write("Content-type: image/jpeg\r\n")
                self.write("Content-length: %s\r\n\r\n" % len(img))
                self.write(img)
                self.served_image_timestamp = time.time()
                yield tornado.gen.Task(self.flush)
            else:
                yield tornado.gen.Task(ioloop.add_timeout, ioloop.time() + interval)
