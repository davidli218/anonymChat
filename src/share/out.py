class ColoredPrint:
    __color_dict = {'black': 30,
                    'red': 31,
                    'green': 32,
                    'yellow': 33,
                    'blue': 34,
                    'magenta': 35,  # 洋红色
                    'cyan': 36,  # 青色
                    'white': 37
                    }

    def __init__(self, text: str, color=None, end='\n'):
        if color is None:
            print(text, end=end)
        elif color not in self.__color_dict:
            ColoredPrint(f'Warning: color:{color} is not valid', 'yellow')
            print(text, end=end)
        else:
            print(f"\033[{self.__color_dict[color]}m{text}\033[0m", end=end)
