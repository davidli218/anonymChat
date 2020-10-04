import sys
import time
import threading
import socket
import json
from hashlib import md5
from typing import List

import utils_c
from pretty_print import PrettyPrint as Pprint

G_PAIRING_PORT = 10080  # <客户端> 连接服务器 </端口>
G_MASSAGE_RECV_PORT = 22218  # <客户端> 收信 </端口>
G_MASSAGE_SEND_PORT = 30141  # <客户端> 送信 </端口>
G_SERVER_MASSAGE_ADDR = None  # <服务器> 送信 </地址>


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
        self.__nickname = self.__input_nickname()

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

    def __conn_server(self) -> bool:
        """ 连接服务器 """
        self.__pairing_socket.settimeout(2)

        response_to_server = json.dumps(
            {'time_stamp': time.time(),
             'name': self.__nickname,
             'port': G_MASSAGE_RECV_PORT,
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

    @staticmethod
    def __input_nickname() -> str:
        while True:
            name = input('Please give yourself a nickname(Up to 12 characters):')
            if len(name) < 13:
                return name
            print('Invalid nickname, please change new one')

    @property
    def __server_pair_addr(self) -> tuple:
        return self.__server_ip, self.__server_pair_port

    @property
    def __server_msg_addr(self) -> tuple:
        return self.__server_ip, self.__server_long_conn_port


class Communication:
    def __init__(self):
        self.dest_port = G_SERVER_MASSAGE_ADDR

        sk4send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sk4send.bind(('', G_MASSAGE_SEND_PORT))
        sk4recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sk4recv.bind(('', G_MASSAGE_RECV_PORT))

        ...


class Main:
    class __Cmd:
        def __init__(self, name: List[str], target, has_arg: bool, doc: str):
            self.name = name  # 名称
            self.target = target  # 调用目标
            self.has_arg = has_arg  # 是否需要参数
            self.doc = doc  # 功能描述

    __exit_flag = False

    def __init__(self):
        self.__CMD_SHEET = (
            self.__Cmd(['show'], self.__show, True, '显示状态/信息'),
            self.__Cmd(['help', 'man'], self.__guide, False, '查看帮助页面'),
            self.__Cmd(['exit', 'quit'], self.__exit, False, '退出AnonymChat'),
        )

        while not self.__exit_flag:
            Pprint('anonymChat> ', color='green', end='')
            cmd = input()
            self.__parse_cmd(cmd)

    def __parse_cmd(self, cmd: str):
        """ 解析用户输入 """
        cmd_list = cmd.split()

        if len(cmd_list) == 0:
            return

        for cmd in self.__CMD_SHEET:
            if cmd_list[0] in cmd.name:
                if cmd.has_arg:
                    if cmd_list == 1:
                        print(f"{cmd_list[0]}: Need at least one parameters")
                        cmd.target(['-h'])
                    else:
                        cmd.target(cmd_list[1:])
                else:
                    if (len(cmd_list) != 1 and cmd_list[1] not in ['-h', '--help']) or len(cmd_list) > 2:
                        print(f'Worming: cmd_list[0] does not need parameters')
                    cmd.target()
                return
        print(f"{cmd_list[0]}: command is not exist")

    def __guide(self):
        print('Help:\n查看详细用法请输入 [option] [-h, --help]\n')
        print(f"{'Command':24}{'Need Arg':12}{'Description'}")
        for cmd in self.__CMD_SHEET:
            print(f'{str(cmd.name):24}{str(cmd.has_arg):12}{cmd.doc}')
        print()

    def __exit(self):
        """ 退出AnonymChat """
        self.__exit_flag = True

    def __show(self):
        """ 显示信息 """
        ...


if __name__ == "__main__":
    # 初始化客户端
    client_init()

    # 获取服务器通信端口
    ConnServer()

    # CLI
    Main()
