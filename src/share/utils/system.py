import os
import threading


def clear_screen():
    if 'nt' in os.name:
        os.system('cls')
    elif 'posix' in os.name:
        os.system('clear')
    else:
        print(f'Unknown platform: {os.name}')
        print(f'Please connect with Email: david_ri@163.com')


def print_current_thread():
    print('\n**** Current_Thread ' + '*' * 50)
    for i in threading.enumerate():
        print(i)
    print('*' * 70 + '\n')
