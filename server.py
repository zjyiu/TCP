import socket
from pro import *

if __name__=='__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((Host, Port))
    data,address=s.recvfrom(BUFFER_SIZE)
    p=sr(s)
    p.send_data("test",address[1])






