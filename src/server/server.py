import time
import threading
import socket
import json
from hashlib import md5

import utils_s
from pretty_print import PrettyPrint as Pprint


# NOTICE########################################
# 2020.09.27 01:15 <David Li>                  #
#     Server can only run in windows now...    #
################################################

class NewUserReceptionist:
    __is_shutdown = False

    def __init__(self, bc_port=12000, pr_port=12165, dest_port=10080):
        self.my_name = f'[{self.__class__.__name__} at {id(self)}]'
        self.broadcast_port = bc_port
        self.broadcast_dest_port = dest_port
        self.pairing_port = pr_port

        # init sockets -> broadcast
        self.__broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.__broadcast_socket.bind(('', bc_port))

        # init sockets -> pairing
        self.__pairing_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__pairing_socket.bind(('', pr_port))

        # init threading
        self.__thread_udp_broadcast = threading.Thread(target=self.__udp_broadcast)
        self.__thread_new_user_waiter = threading.Thread(target=self.__new_user_waiter)

        # log
        print(f'SYS:{self.my_name} Has been created successfully')
        print(f'SYS:{self.my_name} Broadcast using port: {bc_port}')
        print(f'SYS:{self.my_name} Pairing using port: {pr_port}')

    def start(self):
        self.__thread_udp_broadcast.start()
        self.__thread_new_user_waiter.start()

        # log
        print(f'SYS:{self.my_name} UDP broadcast started')
        print(f'SYS:{self.my_name} Pairing started')

    def close(self):
        self.__is_shutdown = True
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
        """ UDP广播 用于客户端发现 """
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
        """ 接待新用户 """
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
                     'port': -1}  # TODO: send long connection port to client
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
    server_start_ui()

    """ Server Logic """
    new_gay_waiter = NewUserReceptionist()
    new_gay_waiter.start()

    input()  # Purse
    server_close()
