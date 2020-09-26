import threading
import os

from pretty_print import PrettyPrint as Pprint

ascii_art_title = r"""
                                         _____ _           _     _____                          
                                        /  __ \ |         | |   /  ___|                         
  __ _ _ __   ___  _ __  _   _ _ __ ___ | /  \/ |__   __ _| |_  \ `--.  ___ _ ____   _____ _ __ 
 / _` | '_ \ / _ \| '_ \| | | | '_ ` _ \| |   | '_ \ / _` | __|  `--. \/ _ \ '__\ \ / / _ \ '__|
| (_| | | | | (_) | | | | |_| | | | | | | \__/\ | | | (_| | |_  /\__/ /  __/ |   \ V /  __/ |   
 \__,_|_| |_|\___/|_| |_|\__, |_| |_| |_|\____/_| |_|\__,_|\__| \____/ \___|_|    \_/ \___|_|   
                          __/ |                                                                 
                         |___/
"""


def clear_screen():
    if 'nt' in os.name:
        os.system('cls')
    elif 'posix' in os.name:
        os.system('clear')
    else:
        Pprint(f'Unknown platform: {os.name}', 'red')
        Pprint(f'Please connect with Email: david_ri@163.com', 'red')


def print_current_thread():
    print('\n**** Current_Thread ' + '*' * 50)
    for i in threading.enumerate():
        print(i)
    print('*' * 70 + '\n')
