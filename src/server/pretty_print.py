class PrettyPrint:
    color_dict = {'black': 30,
                  'red': 31,
                  'green': 32,
                  'yellow': 33,
                  'blue': 34,
                  'magenta': 35,  # 洋红色
                  'cyan': 36,  # 青色
                  'white': 37
                  }

    def __init__(self, text: str, color=None):
        if color is None:
            print(text)
        elif color not in self.color_dict:
            PrettyPrint(f'Warning: color:{color} is not valid', 'yellow')
            print(text)
        else:
            print(f"\033[{self.color_dict[color]}m{text}\033[0m")
