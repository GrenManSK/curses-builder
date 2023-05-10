import curses
VERSION = '1.0.0'
AUTHOR = 'GrenManSK'


window = {}
current_row = 0


class OnlyOneCharKey(Exception):
    pass


def init(stdscr_temp):
    global stdscr
    global COLS
    global LINES
    stdscr = stdscr_temp
    COLS = curses.COLS
    LINES = curses.LINES


def string(y: int, x: int, content: str, move: int = 0, refresh: bool = True, register: bool = True) -> None:
    global window
    global current_row
    if y == 'type':
        return
    try:
        stdscr.addstr(y, x, content)
    except curses.error:
        pass
    if register:
        try:
            if window[y] is not None:
                if len(window[y]) < x:
                    window[y] = window[y] + \
                        (x-len(window[y]))*' ' + content
                else:
                    window[y] = window[y][0:x] + content + \
                        window[y][x + len(content):]
        except KeyError:
            window[y] = ' '*x + content
    current_row += move
    if refresh:
        stdscr.refresh()


class builder:

    def __init__(self, *args):
        self.lenght = len(args)
        cin = 0
        comp = 0
        for times, arg in enumerate(args):
            if isinstance(arg, cinput):
                setattr(self, f"zcinput_{cin}", arg())
                cin += 1
            if isinstance(arg, component):
                setattr(self, f"component_{comp}", arg())
                comp += 1

    def reset(self, window):
        for times, content in window.items():
            string(times, 0, content, register=False)

    def build(self):
        for f in dir(self):
            if str(f).startswith('component_'):
                for times, content in eval(f'self.{f}').items():
                    if times == 'type':
                        continue
                    string(times, content[0], content[1])
            elif str(f).startswith('zcinput_'):
                ikey = None
                x = None
                y = None
                border = None
                function = None
                for times, content in eval(f'self.{f}').items():
                    if times == 'type':
                        continue
                    elif times == 'key':
                        if len(content) > 1:
                            raise OnlyOneCharKey(
                                "You must provide a key, not combination")
                        ikey = content
                        continue
                    elif times == 'x':
                        x = content
                        continue
                    elif times == 'y':
                        y = content
                        continue
                    elif times == 'border':
                        border = content
                        continue
                    elif times == 'function':
                        function = content
                        continue
                    string(times, content[0], content[1])
                if border:
                    string(y, x + 1, '_')
                else:
                    string(y, x, ' ')
                inp = False
                vstup = ''
                end = False
                while True:
                    konecna = False
                    if ikey == '' and not inp:
                        inp = True
                        vstup += ikey
                        curses.nocbreak()
                        stdscr.keypad(False)
                        curses.echo()
                        string(y + 1, x, ikey)
                    key = stdscr.getkey()
                    if inp:
                        if not key == '\n':
                            vstup += key
                        else:
                            vstup = vstup.strip() + ' '
                    if key == ikey:
                        inp = True
                        vstup += ikey
                        curses.nocbreak()
                        stdscr.keypad(False)
                        curses.echo()
                        string(y + 1, x, ikey)
                    if key == '\n':
                        konecna = True
                        inp = False
                        curses.cbreak()
                        stdscr.keypad(True)
                        curses.noecho()
                        if border:
                            string(y + 1, x, int(COLS - 1 - x)*'_')
                        else:
                            string(y + 1, x, int(COLS - 1 - x)*' ')
                    if konecna:
                        if not ikey == '':
                            vstup = vstup[1:-1]
                        else:
                            vstup = vstup[:-1]
                        for func in function:
                            to_func = False
                            func_args = None
                            if isinstance(function[func], list):
                                if len(function[func]) == 2:
                                    func_args = function[func][1]
                                    if not isinstance(func_args, list):
                                        raise ValueError()
                                    if func == vstup.split(' ')[0]:
                                        if function[func][1][0] == 'args':
                                            func_args = vstup[len(
                                                func):].split(' ')
                                            func_args = list(
                                                filter(('').__ne__, func_args))
                                        command = function[func][0]
                                        to_func = True
                                elif func == vstup[function[func][0]:function[func][1]]:
                                    to_func = True
                                    if len(function[func][2]) == 2:
                                        if function[func][2][1][0] == 'args':
                                            func_args = vstup.split(
                                                ' ', 1)[1].split(' ')
                                            func_args = list(
                                                filter(('').__ne__, func_args))
                                        else:
                                            func_args = function[func][2][1]
                                            if not isinstance(func_args, list):
                                                raise ValueError()
                                        command = function[func][2][0]
                                    else:
                                        command = function[func][2]
                            else:
                                if func == vstup:
                                    to_func = True
                                    command = function[func]
                            if to_func:
                                if command == 'break':
                                    end = True
                                    break
                                else:
                                    if func_args is not None:
                                        command(*func_args)
                                    else:
                                        command()
                                    break
                        func_args = None
                        vstup = ''
                    if end:
                        break
        return self

    def add(self, *args):
        for times, arg in enumerate(args):
            times += self.lenght
            setattr(self, f"component_{times}", arg())


class component(builder):
    def __init__(self, content: list[str], y: int, x: int, height: int | None = None, width: int | None = None, border: bool = False):
        self.content = content
        self.y = y
        self.x = x
        if height is None:
            self.height = len(content)
        else:
            self.height = height
        if width is None:
            maxim = 0
            for i in content:
                if len(i) > maxim:
                    maxim = len(i)
            self.width = maxim
        else:
            self.width = width
        self.border = border
        if len(self.content) < self.height and not self.border:
            for i in range(self.height - len(self.content)):
                self.content.append('')
        elif len(self.content) < self.height - 2 and self.border:
            for i in range(self.height - len(self.content) - 2):
                self.content.append('')

    def __call__(self) -> dict:
        window = {'type': 'component'}
        if self.border:
            window[self.y] = [self.x, (self.width + 2) * '_']
            window[self.y + self.height + 1] = [self.x,
                                                '|' + (self.width) * '_' + '|']
        number = 0
        times = 0 if not self.border else 1
        for times in range(self.y + times, self.height + self.y + times):
            if not self.border:
                window[self.y + number] = [self.x, self.content[number] +
                                           (self.width - len(self.content[number]))*' ']
            if self.border:
                window[self.y + number + 1] = [self.x, '|' + self.content[number] +
                                               (self.width - len(self.content[number]))*' ' + '|']
            number += 1
        return window


class cinput(builder):

    def __init__(self, y: int, x: int, key: str, function: dict, border: bool = False):
        self.y = y
        self.x = x
        self.border = border
        self.key = key
        self.function = function

    def __call__(self) -> dict:
        window = {'type': 'cinput', 'key': self.key, 'x': self.x +
                  1 if self.border else self.x, 'y': self.y, 'border': self.border, 'function': self.function}
        if self.border:
            window[self.y] = [self.x, (COLS - self.x) * '_']
            window[self.y + 1] = [self.x,
                                  '|' + (COLS - 2  - self.x) * '_' + '|']
        return window
