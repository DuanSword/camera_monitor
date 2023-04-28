"""

Camera 分为背景线程和工作线程，服务器线程

"""

import time
import threading
import traceback
import numpy as np
try:
    from greenlet import getcurrent as get_ident
except ImportError:
    try:
        from thread import get_ident
    except ImportError:
        from _thread import get_ident
from config import HOST,PORT,IMAGE_SIZE
import socket
import cv2



class CameraEvent(object):
    """An Event-like class that signals all active clients when a new frame is
    available.
    """
    def __init__(self):
        self.events = {}

    def wait(self):
        """Invoked from each client's thread to wait for the next frame."""
        ident = get_ident()
        if ident not in self.events:
            # this is a new client
            # add an entry for it in the self.events dict
            # each entry has two elements, a threading.Event() and a timestamp
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    def set(self):
        """Invoked by the camera thread when a new frame is available."""
        now = time.time()
        remove = None
        # 对events按照时间进行排序
        my_list = list(self.events.items())
        sorted_list = sorted(my_list, key=lambda x: -x[1][1])
        self.events = dict(sorted_list)
        # print(self.events[-1])
        for ident, event in self.events.items():
            if not event[0].isSet():
                # if this client's event is not set, then set it
                # also update the last set timestamp to now
                event[0].set()
                event[1] = now
            else:
                # if the client's event is already set, it means the client
                # did not process a previous frame
                # if the event stays set for more than 5 seconds, then assume
                # the client is gone and remove it
                if now - event[1] > 5:
                    remove = ident
        if remove:
            del self.events[remove]

    def clear(self):
        """Invoked from each client's thread after a frame was processed."""
        self.events[get_ident()][0].clear()
        # time.sleep(0.01)


def socket_read(socket):
    total = int.from_bytes(socket.recv(1024), "big")
    socket.send(b"ok")
    count = 0
    end_data = b""
    tmp = 1024
    while count < total:
        data = socket.recv(tmp)
        end_data += data
        count += len(data)
        if (count + 1024) > total:
            tmp = total - count  # 防止读取到下一次数据的包头
    return end_data


class SocketServer:

    def __init__(self,host = HOST,port = PORT):
        print("Socket Server 已启动...")
        self.host = host
        self.port = port
        self.state = 0 # 0：未连接，1：已连接,2: 传输图像
        self.not_connect_img = self.get_connect_img()
        self.client = None
        self.client_addr = ""
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建 socket 对象,TCP连接
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))  # 绑定端口
        self.server.listen(1)  # 同一时刻只能一个客户端
        self.thread_conn() # 启动监听线程

    def get_connect_img(self):
        img = cv2.imread("./images/katong.jpg")
        img = cv2.resize(img,IMAGE_SIZE)
        frame = cv2.imencode('.jpg', img)[1].tobytes()
        return frame

    def connect(self):
        while True:
            print("等待客户端连接...")
            self.client, self.client_addr = self.server.accept()  # 建立客户端连接
            time.sleep(1)
            self.state = 1
            print("客户端连接成功：(%s:%i)" % self.client_addr)

    def close(self):
        # 关闭客户端连接
        self.client.close()
        self.state = 0
        self.client_addr = ""
        self.client = None
        time.sleep(0.001)
        print("客户端断开连接")

    def get_frame(self):
        # 获取一帧数据:
        frame = self.not_connect_img
        if self.state == 1:
            try:
                self.client.send("get a frame".encode("utf-8"))  # 获取大小
                frame = socket_read(self.client)
            except Exception as e:
                traceback.print_exc()
                self.close()
        if len(frame) == 0:
            frame = self.not_connect_img
        return frame

    def thread_conn(self):
        # 开启线程处理连接时间
        t = threading.Thread(target=self.connect, daemon=True, name=self.host)
        t.start()

def read_bi_img(data):
    img = np.asarray(bytearray(data), dtype="uint8")
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)
    return img

class Camera(object):

    def __init__(self,host = HOST,port = 10001):
        """
        Start the background camera thread if it isn't running yet.
        """
        self.thread = None  # background thread that reads frames from camera
        self.frame = None  # current frame is stored here by background thread
        self.last_access = 0  # time of last client access to the camera
        self.socket_server = SocketServer(host = host,port = port)
        self.event = CameraEvent()
        self.run_thread()


    def run_thread(self):
        if self.thread is None:
            self.last_access = time.time()

            # start background frame thread
            self.thread = threading.Thread(target=self._thread)
            self.thread.start()

            # wait until frames are available
            while self.get_frame() is None:
                time.sleep(0)

    def get_frame(self):
        """Return the current camera frame."""
        self.last_access = time.time()
        # wait for a signal from the camera thread
        self.event.wait()
        self.event.clear()
        return self.frame

    def frames(self):
        """" Generator that returns frames from the camera."""
        while self.thread is not None:
            # if self.socket_server.state == 1:
            #     frame = self.socket_server.get_frame()
            # else:
            #     frame = self.socket_server.not_connect_img
            frame = self.socket_server.get_frame()
            # print(read_bi_img(frame).shape)
            yield frame

    def _thread(self):
        """Camera background thread."""
        print('Starting camera thread.')
        frames_iterator = self.frames()
        for frame in frames_iterator:
            self.frame = frame
            self.event.set()  # send signal to clients
            time.sleep(0.001)
            # if there hasn't been any clients asking for frames in
            # the last 10 seconds then stop the thread
            if time.time() - self.last_access > 10:
                frames_iterator.close()
                print('Stopping camera thread due to inactivity.')
                break
        self.thread = None
        print("camera thread 线程已退出...")