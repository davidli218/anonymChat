import sys
import time
import threading
import socket
import json
from hashlib import md5

import utils_c
from pretty_print import PrettyPrint as Pprint

G_PAIRING_PORT = 10080  # <客户端> 连接服务器 </端口>
G_SERVER_MASSAGE_ADDR = None  # <服务器> 送信 </端口>


def client_init():
    """ Client initialization """
    utils_c.clear_screen()
    Pprint(utils_c.ascii_art_title, 'yellow')


class ConnServer:
    __server_ip = None
    __server_broadcast_port = None
    __server_pair_port = None
    __server_long_conn_port = None

    __meg_from_server = None

    def __init__(self):
        self.__pairing_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__pairing_socket.bind(('', G_PAIRING_PORT))  # Server UDP broadcast port

        self.__main_logic()

        self.__pairing_socket.close()

        if self.__server_long_conn_port is None:
            sys.exit()
        else:
            global G_SERVER_MASSAGE_ADDR
            G_SERVER_MASSAGE_ADDR = self.__server_msg_addr

    def __main_logic(self):
        """ 主逻辑 """
        # Get server address automatically
        thread_find_by_bc = threading.Thread(target=self.__find_by_broadcast)
        thread_find_by_bc.start()
        i = 0
        while thread_find_by_bc.is_alive():
            print(f"\rLooking for the Server {[chr(92), '/', '-'][i]}", end='')
            time.sleep(0.15)
            i = (i + 1) % 3
        print()

        # Get server address manually
        if self.__server_ip is None:
            self.__find_by_manual()
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
        self.__pairing_socket.settimeout(8)
        try:
            while True:
                pkg, addr = self.__pairing_socket.recvfrom(1024)  # Blocking
                pkg = pkg.decode('UTF-8').split(';')

                if len(pkg) != 2 or pkg[0] != md5(pkg[1].encode('UTF-8')).hexdigest():  # Filter
                    continue

                msg_dict = json.loads(pkg[1])

                if abs(time.time() - msg_dict['time_stamp']) < 10:  # Check Unix_timestamp
                    self.__server_ip = addr[0]
                    self.__server_broadcast_port = addr[1]
                    self.__server_pair_port = msg_dict['port']
                    break

        except socket.timeout:
            pass

    def __find_by_manual(self):
        print('No server detected automatically, please connect server manually')
        while True:
            addr = input('Enter the server address in IP:Port (like 10.20.71.2:12800):')
            if utils_c.valid_ip_port(addr):
                addr = addr.split(':')
                self.__server_ip = addr[0]
                self.__server_pair_port = int(addr[1])
                break
            print(f'{addr} is invalid address!')

    def __conn_server(self):
        """ 连接服务器 """
        self.__pairing_socket.settimeout(2)

        response_to_server = json.dumps(
            {'time_stamp': time.time(),
             'py_version': sys.version,
             'sys_platform': sys.platform}
        )

        response_to_server = ';'.join([md5(response_to_server.encode('UTF-8')).hexdigest(), response_to_server])

        self.__pairing_socket.sendto(response_to_server.encode('UTF-8'), self.__server_pair_addr)  # 发送连接请求

        try:
            i = addr = pkg = 0
            while addr != self.__server_pair_addr and i < 3:
                pkg, addr = self.__pairing_socket.recvfrom(1024)
                if addr[1] == self.__server_broadcast_port:
                    continue
                i += 1
        except ConnectionResetError:  # Wrong server port
            return False
        except socket.timeout:  # 2 second time out
            return False
        if i >= 3:
            return False

        pkg = pkg.decode('UTF-8').split(';')

        if len(pkg) != 2 or pkg[0] != md5(pkg[1].encode('UTF-8')).hexdigest():
            return False

        msg_dict = json.loads(pkg[1])

        self.__server_long_conn_port = msg_dict['port']
        self.__meg_from_server = msg_dict['message']

        return True

    @property
    def __server_pair_addr(self):
        return self.__server_ip, self.__server_pair_port

    @property
    def __server_msg_addr(self):
        return self.__server_ip, self.__server_long_conn_port


if __name__ == "__main__":
    # 初始化客户端
    client_init()

    # 获取服务器通信端口
    ConnServer()

    print(G_SERVER_MASSAGE_ADDR)
