import time
import threading
import socket
import json

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

        # log
        print(f'SYS:{self.my_name} UDP Broadcast stopped')
        print(f'SYS:{self.my_name} Pairing stopped')
        Pprint(f'SYS:{self.my_name} Is closed', 'yellow')

    def __udp_broadcast(self):
        """ UDP广播 用于客户端发现 """
        broadcast_dest = (socket.gethostbyname(socket.gethostname()).rsplit('.', 1)[:-1][0] + '.255',
                          self.broadcast_dest_port)
        while True:
            pair_id = json.dumps(['AnCs',  # 标识头
                                  int(time.time() / 5),  # 配对码
                                  self.pairing_port])  # 服务器配对端口
            try:
                self.__broadcast_socket.sendto(pair_id.encode('utf-8'), broadcast_dest)
                time.sleep(3)
            except OSError as e:
                if not self.__is_shutdown:
                    raise OSError(e)
                return

    def __new_user_waiter(self):
        """ 接待新用户 """
        while True:
            try:
                msg, addr = self.__pairing_socket.recvfrom(1024)  # 等待用户连接
            except OSError as e:
                if not self.__is_shutdown:
                    raise OSError(e)
                return

            try:
                msg = json.loads(msg.decode('utf-8'))
                if msg['head'] != 'AnCl' or len(msg) != 4:
                    continue
            except json.decoder.JSONDecodeError:
                continue

            if abs(time.time() / 5 - int(msg['v_code'])) < 10:
                Pprint(f'{addr} Joined the server successfully!'
                       f'\tOS:{msg["sys_platform"]}\tPython:{msg["py_version"].split()[0]}', 'green')

                response = json.dumps({'message': 'Welcome',
                                       'msg_port': -1})  # TODO: send long connection port to client

                self.__pairing_socket.sendto(response.encode('utf-8'), addr)


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
