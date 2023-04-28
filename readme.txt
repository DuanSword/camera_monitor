版本V1

说明
1.使用Socket进行视频流的传输，每台设备都是一个socket client
2.使用多线程处理视频读取与传输
3.使用Flask作为服务器


TODO 列表:
1 增加多个设备（线程池） (done 非线程池)
2 增加缓冲，减少传输速度的损失
3 增加录制和保存按钮
4 改为使用UDP传输
5 监控录屏，从网上下载，Socket传输 
6 只有在当前有网页在浏览的时候才进行数据传输 (done)
7 增加数据库的设计

参考：
https://github.com/zhuohengfeng/Flask_Camera_Monitor