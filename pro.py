import functools
import select
from random import random

Host = '127.0.0.1'
Port = 12340

BUFFER_SIZE = 2048
WINDOWS_LENGTH = 10
MAX_TIME = 3

class cube:
    def __init__(self, s, n=0):
        #序列号
        self.num = str(n)
        #是否被发送
        self.state = 0
        #是否确认接收
        self.isack = 0
        #数据
        self.msg = s

    #发送格式：序列号  数据
    def __str__(self):
        return self.num + '  ' + self.msg

class gbn:
    def __init__(self, s):
        self.s = s

    def send_data(self, path, port):
        #记录时间
        time = 0
        #记录进入窗口的分组数
        num = 0
        #窗口
        data_windows = []
        with open(path, 'r') as f:
            while True:
                #超时
                if time > MAX_TIME:
                    print("time out")
                    #窗口中的分组全部重发
                    for data in data_windows:
                        data.state = 0
                #尽可能地将窗口装满
                while len(data_windows) < WINDOWS_LENGTH:
                    line = f.readline().strip()
                    if not line:
                        break
                    c = cube(line, num)
                    data_windows.append(c)
                    num += 1
                #窗口为空，结束测试
                if not data_windows:
                    self.s.sendto('test over!'.encode(), (Host, port))
                    print('test over!')
                    break
                #将需要发送的分组发送出去
                for data in data_windows:
                    if data.state == 0:
                        self.s.sendto(str(data).encode(), (Host, port))
                        print("send num:" + data.num + "  " + "msg:" + data.msg)
                        data.state = 1
                readable, writeable, errors = select.select([self.s, ], [], [], 1)
                if len(readable) > 0:
                    #收到分组时间重置为0
                    time = 0
                    mesg, addr = self.s.recvfrom(BUFFER_SIZE)
                    message = mesg.decode()
                    print('receive' + message)
                    for i in range(len(data_windows)):
                        if message == data_windows[i].num:
                            #将已经确认的分组从窗口中删除
                            data_windows = data_windows[i + 1:]
                            break
                else:
                    #未收到分组，时间加一
                    time += 1

    def recv_data(self):
        #上一个被确认的分组
        last_ack = -1
        #用来存储数据
        datalist=[]
        while True:
            readable, writeable, errors = select.select([self.s, ], [], [], 1)
            if len(readable) > 0:
                message, address = self.s.recvfrom(BUFFER_SIZE)
                message=message.decode()
                #收到结束信号，结束测试
                if message== 'test over!':
                    break
                #得到序列号
                ack = message.split('  ')[0]
                #得到数据
                m=message.split('  ')[1]
                print('receive num' + ack + '  msg:' + message.split('  ')[1])
                #收到预期的分组
                if last_ack == int(ack) - 1:
                    #20%的概率丢包
                    if random() < 0.2:
                        print('ACK loss')
                        continue
                    #为丢包，则向服务器返回确认信息，打印得到的数据
                    self.s.sendto(ack.encode(), address)
                    print('ACK' + ack)
                    #将数据保存
                    datalist.append(m)
                    #更新最后被确认的分组
                    last_ack = int(ack)
                else:
                    #未收到预期分组，就将最后一个确认的分组信息传给服务器
                    self.s.sendto(str(last_ack).encode(), address)
                    print('ACK' + str(last_ack))
        #打印收到的数据
        for data in datalist:
            print(data)


class sr:
    def __init__(self, s):
        self.s = s

    def send_data(self, path, port):
        #记录时间
        time = 0
        #记录进入窗口的分组数组
        num = 0
        #窗口
        data_windows = []
        with open(path, 'r') as f:
            while True:
                #超时
                if time > MAX_TIME:
                    print("time out")
                    for data in data_windows:
                        #将未被确认接受的分组发送
                        if data.isack == 0:
                            data.state = 0
               #尽可能将窗口装满
                while len(data_windows) < WINDOWS_LENGTH:
                    line = f.readline().strip()
                    if not line:
                        break
                    c = cube(line, num)
                    data_windows.append(c)
                    num += 1
                #窗口为空，结束测试
                if not data_windows:
                    self.s.sendto('test over!'.encode(), (Host, port))
                    print('test over!')
                    break
                #发送需要发送的分组
                for data in data_windows:
                    if data.state == 0:
                        self.s.sendto(str(data).encode(), (Host, port))
                        print("send num:" + data.num + "  " + "msg:" + data.msg)
                        data.state = 1
                readable, writeable, errors = select.select([self.s, ], [], [], 1)
                if len(readable) > 0:
                    #收到分组时间重置为0
                    time = 0
                    isallack = 1
                    #判断哪些分组可以被删除
                    limit = len(data_windows)
                    mesg, addr = self.s.recvfrom(BUFFER_SIZE)
                    print('receive' + mesg.decode())
                    mesg = mesg.decode()
                    #先将确认的分组的信息更新
                    for i in range(len(data_windows)):
                        if mesg == data_windows[i].num:
                            data_windows[i].isack = 1
                            isallack &= 1
                    #将第一个未被确认的分组之前的分组去除
                    for i in range(len(data_windows)):
                        if  data_windows[i].isack==0:
                            limit=i
                            break
                    data_windows = data_windows[limit:]
                else:
                    #未收到分组，时间加一
                    time += 1

    def recv_data(self):
        #用来储存数据
        datalist = []
        while True:
            readable, writeable, errors = select.select([self.s, ], [], [], 1)
            if len(readable) > 0:
                message, address = self.s.recvfrom(BUFFER_SIZE)
                #收到结束信号，结束测试
                if message.decode() == 'test over!':
                    break
                #得到序列号
                ack = message.decode().split('  ')[0]
                #得到数据
                data = message.decode().split('  ')[1]
                print('receive num: ' + ack + '  msg: ' + data)
                #20%的概率丢包
                if random() < 0.2:
                    print('ACK loss')
                    continue
                #将接收到的分组保存
                c = cube(data, ack)
                datalist.append(c)
                # 将保存到分组排序
                datalist.sort(key=functools.cmp_to_key(lambda x, y: int(x.num) - int(y.num)))
                #将确认信息发送给服务器
                self.s.sendto(str(ack).encode(), address)
                print('ACK ' + str(ack))
        #打印收到的数据
        for data in datalist:
            print(data.msg)
