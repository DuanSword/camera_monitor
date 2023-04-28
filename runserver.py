#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, Response
import threading
from tools import Camera
from config import HOST
import time
app = Flask(__name__,static_folder='static')


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

def gen(camera):
    """Video streaming generator function."""
    camera.run_thread()
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    print(threading.get_ident(),"线程启动！")
    return Response(gen(camera1),
                    mimetype='multipart/x-mixed-replace; boundary=frame')



@app.route('/video_feed2')
def video_feed2():
    """Video streaming route. Put this in the src attribute of an img tag."""
    print(threading.get_ident(),"线程启动！")
    return Response(gen(camera2),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    camera1 = Camera(port = 10001)
    camera2 = Camera(port = 10002)
    app.run(host=HOST, threaded=True)
