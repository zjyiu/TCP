import socket
from pro import *

addr = (Host, Port)

if __name__ == '__main__':
    # 建立客户端UDP套接字
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.sendto('test'.encode(),addr)
    p = sr(s)
    p.recv_data()
    print('test over!')

