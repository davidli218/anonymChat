import sys
import time
import threading
import socket
import json

import utils_c
from pretty_print import PrettyPrint as Pprint


class ConnServer:
    __server_ip = None
    __server_broadcast_port = None
    __server_pair_port = None
    __server_long_conn_port = None

    __meg_from_server = None

    def __init__(self):
        self.__pairing_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__pairing_socket.bind(('', 10080))  # Server UDP broadcast port

        self.__main_logic()

        self.__pairing_socket.close()

        if self.__server_long_conn_port is None:
            sys.exit()

    def __main_logic(self):
        """ 主逻辑 """
        bar_list = ['\\', '/', '-']
        i = 0

        # Get server address automatically
        thread_find_by_bc = threading.Thread(target=self.__find_by_broadcast)
        thread_find_by_bc.start()

        while thread_find_by_bc.is_alive():
            print(f'\rLooking for the Server {bar_list[i]}', end='')
            time.sleep(0.15)
            i = (i + 1) % 3
        print()

        # Get server address manually
        if self.__server_ip is None:
            print('No server detected automatically, please connect server manually')
            while True:
                addr = input('Enter the server address in IP:Port (like 10.20.71.2:12800):')
                if utils_c.valid_ip_port(addr):
                    addr = addr.split(':')
                    self.__server_ip = addr[0]
                    self.__server_pair_port = int(addr[1])
                    break
                print(f'{addr} is invalid address!')
        else:
            print(f'Server found in {self.__server_ip}')

        # Connect server
        if self.__conn_server():
            Pprint(f'^_^ Connect with server({self.__server_ip}) successfully', 'cyan')
            print(self.__meg_from_server)
        else:
            print("Server doesn't response.")

    def __find_by_broadcast(self):
        """ 通过UDP广播找到服务器 """
        try:
            while True:
                self.__pairing_socket.settimeout(8)
                msg, addr = self.__pairing_socket.recvfrom(1024)  # blocking
                msg = json.loads(msg.decode('utf-8'))

                if msg[0] != 'AnCs' or len(msg) != 3:  # filter
                    continue
                elif abs(int(time.time() / 5) - int(msg[1]) < 10):  # 校对密钥
                    self.__server_ip = addr[0]
                    self.__server_broadcast_port = addr[1]
                    self.__server_pair_port = msg[2]
                    break

        except socket.timeout:
            pass

    def __conn_server(self):
        """ 连接服务器 """
        self.__pairing_socket.settimeout(2)

        response_to_server = json.dumps({'head': 'AnCl',
                                         'v_code': int(time.time() / 5),
                                         'py_version': sys.version,
                                         'sys_platform': sys.platform})

        self.__pairing_socket.sendto(response_to_server.encode('utf-8'), self.__server_pair_addr)  # 发送连接请求

        try:
            i = addr = msg = 0
            while addr != self.__server_pair_addr and i < 3:
                msg, addr = self.__pairing_socket.recvfrom(1024)
                if addr[1] == self.__server_broadcast_port:
                    continue
                i += 1
        except ConnectionResetError:  # Wrong server port
            return False
        except socket.timeout:  # 2 second time out
            return False
        if i >= 3:
            return False

        msg = json.loads(msg.decode('utf-8'))
        self.__server_long_conn_port = msg['msg_port']
        self.__meg_from_server = msg['message']

        return True

    @property
    def __server_pair_addr(self):
        return self.__server_ip, self.__server_pair_port

    @property
    def server_long_conn_addr(self):
        return self.__server_ip, self.__server_long_conn_port


def client_start_ui():
    utils_c.clear_screen()
    Pprint(utils_c.ascii_art_title, 'yellow')


if __name__ == "__main__":
    client_start_ui()

    long_conn_addr = ConnServer().server_long_conn_addr

    print(long_conn_addr)

    ...
