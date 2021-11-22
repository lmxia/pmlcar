#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun 24 20:10:44 2017

@author: wroscoe

remotes.py

The client and web server needed to control a car remotely.
"""
import os
import os.path
import time
import json
from config import load_config

import tornado.httpserver
import tornado
import tornado.ioloop
import tornado.web
import tornado.gen
import utils
import requests
from parts.miniostore import UpAndDownload
import asyncio


class LocalWebController(tornado.web.Application):
    port = 8887

    def __init__(self,kl=None):
        """
        Create and publish variables needed on many of
        the web handlers.
        """
        print('Starting Car Server...')
        cfg = load_config()

        this_dir = os.path.dirname(os.path.realpath(__file__))
        self.static_file_path = os.path.join(this_dir, 'templates', 'static')
        self.cloud_ip = "http://" + cfg.CLOUD_IP + ":30007"
        self.data_path = cfg.DATA_PATH
        self.task_id = None
        self.minio_endpoint = cfg.CLOUD_IP +":9000"
        self.access_key = cfg.ACCESS_KEY
        self.secret_key = cfg.SECRET_KEY
        self.minio_client = UpAndDownload(self.data_path,self.minio_endpoint,self.access_key,self.secret_key)
        self.kl = kl

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
            (r"/train", TrainAPI),
            (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": self.static_file_path}),
            (r"/upload", UpDataAPI),
            (r"/status", StatusAPI),
            (r"/download",DownloadAPI),
        ]

        settings = {'debug': True}
        super().__init__(handlers, **settings)

    def update(self):
        """ Start the tornado web server. """
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.port = int(self.port)
        self.listen(self.port)
        instance = tornado.ioloop.IOLoop.instance()
        # instance.add_callback(self.say_hello)
        instance.start()

    def run_threaded(self, img_arr=None):
        self.img_arr = img_arr
        return self.angle, self.throttle, self.mode, self.recording

    def shutdown(self):
        pass


class UpDataAPI(tornado.web.RequestHandler):
    def post(self):
        up = self.application.minio_client
        up.upload_data()

class DownloadAPI(tornado.web.RequestHandler):
    def post(self):
        download = self.application.minio_client
        download.download_data("model","keras_metadata.pb")
        download.download_data("model","saved_model.pb")
        download.download_data("model","variables/variables.data-00000-of-00001")
        download.download_data("model","variables/variables.index")
        self.application.kl.load(os.path.join(os.path.expanduser(self.application.data_path),"model"))




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


class TrainAPI(tornado.web.RequestHandler):
    def post(self):
        # data_path = self.get_body_argument("data_path")
        data_path = self.application.data_path
        if self.application.task_id is not None:
            return self.write("task is running.")
        if data_path is not None:
            url = os.path.join(self.application.cloud_ip, "train")
            data = {
                "data_path": data_path
            }
            response = requests.post(url=url, data=data)
            response_data = json.loads(response.content.decode())
            self.application.task_id = response_data['task_id']
            return self.write(response.content)


class StatusAPI(tornado.web.RequestHandler):
    def post(self):
        task_id = self.application.task_id
        if task_id is not None:
            url = os.path.join(self.application.cloud_ip, "status")
            data = {
                "task_id": task_id
            }
            response = requests.post(url=url, data=data)
            response_data = json.loads(response.content.decode())
            state = response_data['state']
            if state == "SUCCESS":
                self.application.task_id = None
            if state == "FAILED":
                self.application.task_id = None
            return self.write(response.content)
        else:
            data = {
                "state":"not running a task",
                "epoch": "null",
                "loss": "null"
            }
            return self.write(data)


class VideoAPI(tornado.web.RequestHandler):
    '''
    Serves a MJPEG of the images posted from the vehicle.
    '''

    async def get(self):

        self.set_header("Content-type",
                        "multipart/x-mixed-replace;boundary=--boundarydonotcross")

        served_image_timestamp = time.time()
        my_boundary = "--boundarydonotcross\n"
        while True:

            interval = .01
            if served_image_timestamp + interval < time.time() and \
                    hasattr(self.application, 'img_arr'):

                img = utils.arr_to_binary(self.application.img_arr)
                self.write(my_boundary)
                self.write("Content-type: image/jpeg\r\n")
                self.write("Content-length: %s\r\n\r\n" % len(img))
                self.write(img)
                served_image_timestamp = time.time()
                try:
                    await self.flush()
                except tornado.iostream.StreamClosedError:
                    pass
            else:
                await tornado.gen.sleep(interval)


if __name__ == '__main__':
    ctr = LocalWebController()
    ctr.update()
