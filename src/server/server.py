import sys
import time
import threading
import socket
import json
from hashlib import md5

import utils_s
from pretty_print import PrettyPrint as Pprint

G_BROADCAST_PORT = 12000  # <服务器> 广播配对信息 </端口>
G_PAIRING_PORT = 12165  # <服务器> 接受连接请求 </端口>
G_CLIENT_PAIRING_PORT = 10080  # <客户端> 发现并连接服务器 </端口>
G_MASSAGE_PORT = 20218  # <服务器> 稳定通讯 </端口>


class NewUserReceptionist:
    """ 广播服务器信息，处理客户端连接请求 """
    __is_shutdown = False

    def __init__(self):
        self.my_name = f'[{self.__class__.__name__} at {id(self)}]'
        self.broadcast_port = G_BROADCAST_PORT
        self.broadcast_dest_port = G_CLIENT_PAIRING_PORT
        self.pairing_port = G_PAIRING_PORT
        self.message_port = G_MASSAGE_PORT

        # init sockets -> broadcast
        self.__broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.__broadcast_socket.bind(('', self.broadcast_port))

        # init sockets -> pairing
        self.__pairing_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__pairing_socket.bind(('', self.pairing_port))

        # init threading
        self.__thread_udp_broadcast = threading.Thread(target=self.__udp_broadcast)
        self.__thread_new_user_waiter = threading.Thread(target=self.__new_user_waiter)

        # log
        print(f'SYS:{self.my_name} Has been created successfully')
        print(f'SYS:{self.my_name} Broadcast using port: {self.broadcast_port}')
        print(f'SYS:{self.my_name} Pairing using port: {self.pairing_port}')

    def start(self):
        self.__thread_udp_broadcast.start()
        self.__thread_new_user_waiter.start()

        # log
        print(f'SYS:{self.my_name} UDP broadcast started')
        print(f'SYS:{self.my_name} Pairing started')

    def close(self):
        self.__is_shutdown = True

        if sys.platform == 'darwin':
            """
            Linux and Windows are very forgiving about calling shutdown() on a closed socket.
            But on Mac OS X shutdown() only succeeds if the OS thinks that the socket is still open,
            otherwise OS X kills the socket.shutdown() statement with:
                socket.error: [Errno 57] Socket is not connected
            """
            try:
                self.__broadcast_socket.shutdown(socket.SHUT_RDWR)
                self.__pairing_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        else:
            self.__broadcast_socket.shutdown(socket.SHUT_RDWR)
            self.__pairing_socket.shutdown(socket.SHUT_RDWR)

        self.__broadcast_socket.close()
        self.__pairing_socket.close()

        self.__thread_new_user_waiter.join()
        self.__thread_udp_broadcast.join()

        # log
        print(f'SYS:{self.my_name} UDP Broadcast stopped')
        print(f'SYS:{self.my_name} Pairing stopped')
        Pprint(f'SYS:{self.my_name} Is closed', 'yellow')

    def __udp_broadcast(self):
        """ UDP Broadcast 用于被客户端发现 """
        broadcast_dest = (socket.gethostbyname(socket.gethostname()).rsplit('.', 1)[:-1][0] + '.255',
                          self.broadcast_dest_port)
        while True:
            msg_dict = json.dumps(
                {'time_stamp': time.time(),  # Unix_timestamp
                 'port': self.pairing_port}  # 服务器配对端口
            )
            bc_pkg = ';'.join([md5(msg_dict.encode('UTF-8')).hexdigest(), msg_dict])

            try:
                self.__broadcast_socket.sendto(bc_pkg.encode('UTF-8'), broadcast_dest)

                for _ in range(6):  # 广播3秒间隔
                    if self.__is_shutdown:
                        return
                    time.sleep(0.5)

            except OSError as e:
                if not self.__is_shutdown:
                    raise OSError(e)
                return

    def __new_user_waiter(self):
        """ Deal with new client connection request """
        while True:
            try:
                pkg, addr = self.__pairing_socket.recvfrom(1024)  # 等待用户连接
                pkg = pkg.decode('UTF-8').split(';')

            except OSError as e:
                if not self.__is_shutdown:
                    raise OSError(e)
                return

            if len(pkg) != 2 or pkg[0] != md5(pkg[1].encode('UTF-8')).hexdigest():
                continue

            msg_dict = json.loads(pkg[1])

            if abs(time.time() - msg_dict['time_stamp']) < 10:
                Pprint(f'{addr} Joined the server successfully!'
                       f'\tOS:{msg_dict["sys_platform"]}\tPython:{msg_dict["py_version"].split()[0]}', 'green')

                response = json.dumps(
                    {'message': 'Welcome',
                     'port': self.message_port}
                )
                response = ';'.join([md5(response.encode('UTF-8')).hexdigest(), response])

                self.__pairing_socket.sendto(response.encode('UTF-8'), addr)


def server_start_ui():
    """ Starting Interface """
    utils_s.clear_screen()
    Pprint(utils_s.ascii_art_title, 'green')
    Pprint(f'Host name:{socket.gethostname()}\t'
           f'Host IP:{socket.gethostbyname(socket.gethostname())}\t'
           f'Pairing by port: 12165', 'cyan')
    print()


def server_close():
    """ Shutdown server """
    Pprint('=' * 32 + 'Server is doing shutdown' + '=' * 32, 'red')
    new_gay_waiter.close()


if __name__ == "__main__":
    """ Starting point """
    server_start_ui()

    """ Server Logic """
    new_gay_waiter = NewUserReceptionist()
    new_gay_waiter.start()

    input()  # Purse
    server_close()
