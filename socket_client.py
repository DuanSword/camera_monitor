#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import time
import traceback
import cv2
import config

class SocketClient:

    def __init__(self,host = config.HOST,port = 10001):
        self.host = host
        self.port = port
        self.image_size = config.IMAGE_SIZE

    def start(self):
        s = socket.socket()  # 创建 socket 对象
        s.connect((self.host, self.port))
        print("连接成功")
        # s.recv(1024).decode("utf-8")  # 等待消息
        # s.send("ok".encode("utf-8"))
        frame_cnt = 0
        cap = cv2.VideoCapture(0)
        while True:
            quest = s.recv(1024).decode("utf-8")
            # 接受到信号
            while quest != "get a frame": continue
            frame_cnt += 1
            t1 = time.time()
            ret, frame = cap.read()
            frame = cv2.resize(frame, self.image_size)
            # 保存视频
            data = cv2.imencode('.jpg', frame)[1].tobytes()
            s.send(len(data).to_bytes(4,"big"))  # 发送数据大小
            s.recv(1024)
            s.sendall(data)
            t2 = time.time()
            # print("send using time: %.5f"%(t2- t1))
            if frame_cnt > 100000:
                break
        s.close()

    def run(self):
        while True:
            try:
                self.start()
            except Exception as e:
                print("连接断开")
                # print(traceback.print_exc())
                time.sleep(1)

if __name__ == "__main__":
    client = SocketClient()
    client.run()

