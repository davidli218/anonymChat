import sys
import time
import threading
import socket
import json
from hashlib import md5

import utils
from utils.out import ColoredPrint

from . import help_doc

G_PAIRING_PORT = 10080  # <本机端口> 接收来自服务器的配对广播 & 承载配对流程
G_MASSAGE_RECV_PORT = 22218  # <本机端口> 用于接收来自服务器的包
G_MASSAGE_SEND_PORT = 30141  # <本机端口> 用于向服务器发送包
G_SERVER_MASSAGE_ADDR = None  # <服务器地址> 服务器的收包地址


def client_init():
    """ Initialize client """
    utils.system.clear_screen()
    ColoredPrint(utils.art.ascii_art_title_4client, 'yellow')


class ConnServer:
    """ Find & Connect the server """
    __server_ip = None
    __server_broadcast_port = None
    __server_pairing_port = None
    __server_message_port = None

    __meg_from_server = None

    def __init__(self):
        self.__nickname = self.__input_nickname()

        self.__pairing_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__pairing_socket.bind(('', G_PAIRING_PORT))

        self.__main()

        self.__pairing_socket.close()

        if self.__server_message_port is None:
            sys.exit()
        else:
            global G_SERVER_MASSAGE_ADDR
            G_SERVER_MASSAGE_ADDR = self.__server_msg_addr

    def __main(self):
        """ Main logic of find & Connect the server """

        # Get server address automatically -- {
        thread_find_by_bc = threading.Thread(target=self.__find_by_broadcast)
        thread_find_by_bc.start()

        i = 0  # Beautiful waiting animation
        while thread_find_by_bc.is_alive():
            print(f"\rLooking for the Server {[chr(92), '/', '-'][i]}", end='')
            time.sleep(0.15)
            i = (i + 1) % 3
        print()
        # } --

        # Get server address manually -- {
        if self.__server_ip is None:
            self.__find_by_manual()
        # } --

        # Connect server -- {
        if self.__conn_server():
            ColoredPrint(f'^_^ Connect with server({self.__server_ip}) successfully', 'cyan')
            print(self.__meg_from_server)
        else:
            print("Server doesn't response.")
        # } --

    def __find_by_broadcast(self):
        """ Find the server automatically via UDP broadcast """
        self.__pairing_socket.settimeout(8)
        start_time = time.time()

        try:
            while time.time() - start_time < 8:
                pkg, addr = self.__pairing_socket.recvfrom(1024)  # Blocking

                msg_dict = self.__unpacker(pkg)
                if not msg_dict:
                    continue

                if abs(time.time() - msg_dict['time_stamp']) < 10:  # Check Unix_timestamp
                    self.__server_ip = addr[0]
                    self.__server_broadcast_port = addr[1]
                    self.__server_pairing_port = msg_dict['port']
                    break
        except socket.timeout:
            pass

    def __find_by_manual(self):
        """ Find the server manually via user input address """
        print('No server detected automatically, please connect the server manually')
        while True:
            addr = input('Enter the server address in IP:Port (like 10.20.71.2:9999):')
            if utils.validator.valid_ip_port(addr):
                addr = addr.split(':')
                self.__server_ip = addr[0]
                self.__server_pairing_port = int(addr[1])
                break
            print(f'{addr} is invalid address!')

    def __conn_server(self) -> bool:
        """ Connecting to the server """
        self.__pairing_socket.settimeout(2)

        response_to_server = {'time_stamp': time.time(),
                              'name': self.__nickname,
                              'port': G_MASSAGE_RECV_PORT,
                              'py_version': sys.version,
                              'sys_platform': sys.platform}

        self.__pairing_socket.sendto(self.__packager(response_to_server), self.__server_pair_addr)  # 发送连接请求

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

        msg_dict = self.__unpacker(pkg)
        if not msg_dict:
            return False

        self.__server_message_port = msg_dict['port']
        self.__meg_from_server = msg_dict['message']
        return True

    @staticmethod
    def __unpacker(pack: bytes) -> dict:
        """Unpacker

        :param pack: [ md5(JSON(content)) + ';' + JSON(content) ].UTF-8
        :return: Content
        """
        pack = pack.decode('UTF-8').split(';')

        if len(pack) != 2 or pack[0] != md5(pack[1].encode('UTF-8')).hexdigest():
            return {}

        return json.loads(pack[1])

    @staticmethod
    def __packager(content: dict) -> bytes:
        """Packager

        :param content: Content
        :return: [ md5(JSON(content)) + ';' + JSON(content) ].UTF-8
        """
        content = json.dumps(content)
        content = ';'.join([md5(content.encode('UTF-8')).hexdigest(), content])

        return content.encode('UTF-8')

    @staticmethod
    def __input_nickname() -> str:
        """ Get user nickname """
        while True:
            name = input('Please give yourself a nickname(Up to 12 characters):')
            if len(name) < 13:
                return name
            print('Invalid nickname, please change new one')

    @property
    def __server_pair_addr(self) -> tuple:
        """ Server pairing address """
        return self.__server_ip, self.__server_pairing_port

    @property
    def __server_msg_addr(self) -> tuple:
        """ Server message address """
        return self.__server_ip, self.__server_message_port


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
        def __init__(self, name: [str], target, has_arg: bool, doc: str):
            self.name = name  # 名称
            self.target = target  # 调用目标
            self.has_arg = has_arg  # 是否需要参数
            self.doc = doc  # 功能描述

    __exit_flag = False

    def __init__(self):
        self.__CMD_SHEET = (
            self.__Cmd(['help', 'man'], self.__guide, False, '查看帮助页面'),
            self.__Cmd(['exit', 'quit'], self.__exit, False, '退出AnonymChat'),
            self.__Cmd([], None, False, ''),
        )

        while not self.__exit_flag:
            ColoredPrint('anonymChat> ', color='green', end='')
            self.__input_parser(input())

    def __input_parser(self, user_input: str):
        """ User input parser """
        if len(user_input) == 0:  # 处理空白输入
            return

        cmd_name = user_input.split()[0]
        cmd_para = user_input.split()[1:]

        cmd = None
        for cmd in self.__CMD_SHEET:
            if cmd_name.lower() in cmd.name:
                break

        if not cmd.name:
            print(f"{cmd_name}: command is not exist")

        elif cmd.has_arg and len(cmd_para):
            print(f"{cmd_name}: Need at least one parameters")
            print(f"input '{cmd_name} -h' to find the usage")

        elif not cmd.has_arg and (len(cmd_para) > 1 or (len(cmd_para) and cmd_para[0] not in ['-h', '--help'])):
            print(f'{cmd_name} does not need parameters')
            print(f"Input '{cmd_name} -h' to find the usage")

        else:
            cmd.target(cmd_para)

    def __guide(self, args: list):
        """ AnonymChat Help Page """
        if not args:
            print('Help:\nFind the detailed usage by [option] [-h, --help]\n')
            print(f"{'Command':24}{'Need Arg':12}{'Description'}")
            for cmd in self.__CMD_SHEET[:-1]:
                print(f"{str(cmd.name).replace(chr(39), ''):24}{str(cmd.has_arg):12}{cmd.doc}")
            print()

        else:
            print(help_doc.guide_help_doc)

    def __exit(self, args: list):
        """ Exit AnonymChat """
        if not args:
            while True:
                choice = input('Do you want to quit AnonymChat(Y/N): ').upper()
                if choice == 'Y':
                    self.__exit_flag = True
                    return
                elif choice == 'N':
                    return
                else:
                    print("Invalid input, only 'Y' and 'N' is available)")

        else:
            print(help_doc.exit_help_doc)


def execute():
    # 初始化客户端
    client_init()

    # 获取服务器通信端口
    ConnServer()

    # CLI
    Main()
