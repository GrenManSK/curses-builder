import contextlib
import curses
import copy
from random import randint
import Levenshtein
import win32clipboard

VERSION = "1.2.0"
AUTHOR = "GrenManSK"

__all__ = ["builder", "component", "cinput"]


def get_id(long: int = 10) -> int:
    return "".join(str(randint(0, 9)) for _ in range(long))


window = {}
current_row = 0

global in_func
history = {}
history_number = 0
in_func = False
func_reset = False
last_command_history = {}
ids = {}
current_id = None


class OnlyOneCharKey(Exception):
    pass


def init(stdscr_temp):
    global stdscr
    global COLS
    global LINES
    stdscr = stdscr_temp
    COLS = curses.COLS
    LINES = curses.LINES


def string(
    y: int,
    x: int,
    content: str,
    move: int = 0,
    refresh: bool = True,
    register: bool = True,
) -> None:
    global window
    global current_row
    if y == "type":
        return
    try:
        stdscr.addstr(y, x, content, curses.color_pair(1))
    except curses.error:
        with contextlib.suppress(curses.error):
            stdscr.addstr(y, x, content)
    if register:
        try:
            if window[y] is not None:
                if len(window[y]) < x:
                    window[y] = window[y] + (x - len(window[y])) * " " + content
                else:
                    window[y] = window[y][:x] + content + window[y][x + len(content) :]
        except KeyError:
            window[y] = " " * x + content
    current_row += move
    if refresh:
        stdscr.refresh()


class builder:
    def __init__(self, *args):
        self.length = len(args)
        cin = 0
        comp = 0
        for times, arg in enumerate(args):
            if isinstance(arg, cinput):
                setattr(self, f"zcinput_{cin}", arg())
                cin += 1
            if isinstance(arg, component):
                setattr(self, f"component_{comp}", arg())
                comp += 1

    def add_history(self, window_temp):
        global history_number
        global func_reset
        with contextlib.suppress(KeyError):
            if history[history_number] == history[history_number - 1]:
                return
        if not in_func and not func_reset:
            history[history_number] = copy.deepcopy(window_temp)
            history_number += 1
            window = copy.deepcopy(window_temp)

    def reset(self, window_temp):
        global history_number
        global window
        global func_reset
        for i in range(LINES):
            string(i, 0, COLS * " ", register=False)
        for times, content in window_temp.items():
            string(times, 0, content, register=False)
        self.add_history(window_temp)

    def restore(self, command):
        for y in command:
            x = command[y][0]
            content = len(command[y][1].strip()) * " "
            string(
                y,
                x,
                content,
            )

    def build(self):
        global history_number
        global in_func
        global func_reset
        global current_id
        for f in dir(self):
            if str(f).startswith("component_"):
                for times, content in eval(f"self.{f}").items():
                    if times == "type":
                        continue
                    string(times, content[0], content[1])
                    if in_func:
                        last_command_history[ids[current_id]] = {}
                        last_command_history[ids[current_id]][times] = [
                            content[0],
                            content[1],
                        ]
                self.add_history(window)
            elif str(f).startswith("zcinput_"):
                ikey = None
                x = None
                y = None
                border = None
                function = None
                width = None
                for times, content in eval(f"self.{f}").items():
                    if times == "type":
                        continue
                    elif times == "key":
                        if len(content) > 1:
                            raise OnlyOneCharKey(
                                "You must provide a key, not combination"
                            )
                        ikey = content
                        continue
                    elif times == "x":
                        x = content
                        continue
                    elif times == "y":
                        y = content
                        continue
                    elif times == "border":
                        border = content
                        continue
                    elif times == "function":
                        function = content
                        continue
                    elif times == "limit":
                        limit = content
                        continue
                    elif times == "help":
                        help = content
                        continue
                    elif times == "nof":
                        nof = content
                        continue
                    elif times == "width":
                        width = content
                        continue
                    string(times, content[0], content[1])
                if border:
                    string(y, x + 1, "_")
                else:
                    string(y, x, " ")
                inp = False
                vstup = ""
                end = False
                history_in_row = 0
                last_command = None
                self.add_history(window)
                pocet = 0
                key = ""
                _func = None
                is_func = False
                arg_num = 0
                arg_num_hist = -1
                arg_hist = {}
                __func_to_use = ""
                number_of_tabs_hist = 0
                _in_tab = False
                _in_tab_num = 0
                main_arg = None
                select_all = False
                while True:
                    string(y, x, (COLS - x) * " ")
                    if border:
                        string(y - 1, x, (COLS - x) * "_")
                    else:
                        string(y - 1, x, (COLS - x) * " ")
                    if len(vstup) > COLS:
                        string(y, x, vstup[abs(COLS - len(vstup)) :])
                    else:
                        string(y, x, vstup)
                    func_reset = False
                    konecna = False
                    if help and len(vstup) == 1:
                        string(y - 1, x + 2, help)
                        string(y, x, vstup)
                    if not vstup[1:pocet] in function.keys() and is_func:
                        string(y - 1, x, (COLS - x) * " ")
                        string(y, x + len(_func), "")
                        is_func = False
                        arg_num = 0
                        arg_num_hist = -1
                        arg_hist = {}
                    if vstup[1:].split(" ")[0].split("\t")[0] in function.keys():
                        _func = vstup[1:].split(" ")[0].split("\t")[0]
                        if function[_func] == "help":
                            number_of_tabs = vstup.count("\t")
                            if number_of_tabs_hist == 0 and key in [
                                "KEY_BTAB",
                                "KEY_B1",
                            ]:
                                number_of_tabs = len(function.keys()) - 1
                                vstup += number_of_tabs * "\t"
                            while number_of_tabs > len(function.keys()) - 1:
                                number_of_tabs = 0
                                vstup = vstup.split(" ")[0].split("\t")[0]
                            indent = 4
                            vstup = vstup.split(" ")[0]
                            _help = ""
                            for times, i in enumerate(function.keys()):
                                _help += f" {i} |"
                                if times < number_of_tabs:
                                    indent += len(i) + 3
                                elif times == number_of_tabs:
                                    indent += int(len(i) / 2)
                                    __func_to_use = i
                            _help = _help[:-1]
                            indent -= 1
                            string(
                                y - 1,
                                x + len(vstup.split(" ")[0].split("\t")[0]),
                                _help,
                            )
                            string(
                                y,
                                x
                                + indent
                                + len(vstup.split(" ")[0].split("\t")[0])
                                - 2,
                                "^",
                            )
                            string(y, x, vstup.split("\t")[0])
                            number_of_tabs_hist = number_of_tabs
                        elif not _func in ["q", "r"]:
                            is_func = True
                            pocet = len(_func) + 1
                    if is_func:
                        _vstup = list(filter(("").__ne__, vstup.split(" ")))
                        increment = 1 if vstup.split(" ")[-1] == "" else 0
                        count = 0
                        _increment = 0
                        for times, i in enumerate(vstup.split(" ")):
                            if i == "":
                                if times == 0 or times == len(vstup) - 1:
                                    continue
                                count += 1
                            if i != "":
                                _increment += count
                                count = 0
                        _increment -= 1
                        if increment == 1:
                            _vstup.append("")
                        arg_num = len(_vstup) - 2
                        if arg_num == -1:
                            arg_num = 0
                        nam = vstup.split(" ")
                        if len(nam) == 1:
                            posun = len(_func) + 2 + _increment
                        else:
                            posun = (
                                sum([len(i) for i in vstup.split(" ")[:-1]])
                                + 2
                                + _increment
                                + arg_num
                            )
                        try:
                            if key in ["\t", "KEY_BTAB"]:
                                if isinstance(function[_func][4][arg_num], list):
                                    _help = function[_func][4][arg_num]
                                elif isinstance(function[_func][4][arg_num], dict):
                                    _help = function[_func][4][arg_num][main_arg]
                                string(y - 1, COLS - 14, "Running Engine")
                                if isinstance(_help[0], list) and not _in_tab:
                                    _return = search_engine_double(
                                        _vstup[arg_num + 1], _help
                                    )
                                if isinstance(_help[0], str) and not _in_tab:
                                    _return = search_engine(_vstup[arg_num + 1], _help)
                                string(y - 1, COLS - 14, "              ")
                                if _return is not None:
                                    if key == "KEY_BTAB":
                                        _in_tab_num -= 2
                                    if _in_tab_num >= len(_return):
                                        _in_tab_num = 0
                                    vstup = (
                                        vstup.rsplit(" ", 1)[0]
                                        + " "
                                        + _return[_in_tab_num].replace(" ", "_")
                                    )
                                    string(y, x, (COLS - x) * " ")
                                    string(y, x, vstup)
                                    _in_tab = True
                                    _in_tab_num += 1
                            else:
                                _in_tab = False
                                _in_tab_num = 0
                        except IndexError:
                            _in_tab = False
                            _in_tab_num = 0
                        if _in_tab and key == "\t":
                            vstup = vstup.replace("\t", " ")
                        if arg_num != arg_num_hist:
                            if border:
                                string(y - 1, x, (COLS - x) * "_")
                            else:
                                string(y - 1, x, (COLS - x) * " ")
                            if arg_num < arg_num_hist:
                                try:
                                    if isinstance(
                                        function[_func][3][arg_num_hist], dict
                                    ):
                                        arg_hist.pop(
                                            function[_func][3][arg_num_hist][main_arg]
                                        )
                                    else:
                                        arg_hist.pop(function[_func][3][arg_num_hist])
                                except IndexError:
                                    pass
                            arg_num_hist = arg_num
                        try:
                            if isinstance(function[_func][3][arg_num], dict):
                                arg_hist[function[_func][3][arg_num][main_arg]] = (
                                    x + posun
                                )
                            else:
                                arg_hist[function[_func][3][arg_num]] = x + posun
                            for times, i in arg_hist.items():
                                string(y - 1, x + i, times)
                            if isinstance(function[_func][3][arg_num], dict):
                                string(
                                    y - 1,
                                    x + posun,
                                    function[_func][3][arg_num][main_arg],
                                )
                            else:
                                string(y - 1, x + posun, function[_func][3][arg_num])
                            more_arg = ""
                            for i in range(arg_num + 1, len(function[_func][3])):
                                if isinstance(function[_func][3][i], dict):
                                    try:
                                        if (
                                            vstup.split(" ")[1]
                                            in function[_func][3][i].keys()
                                        ):
                                            more_arg += (
                                                " "
                                                + function[_func][3][i][
                                                    vstup.split(" ")[1]
                                                ]
                                                + " |"
                                            )
                                            main_arg = vstup.split(" ")[1]
                                    except IndexError:
                                        pass
                                else:
                                    more_arg += " " + function[_func][3][i] + " |"

                            more_arg = more_arg[:-1]
                            more_posun = (
                                len(vstup) - posun - len(function[_func][3][arg_num])
                            )
                            if len(more_arg) > COLS - x - more_posun - posun - 3:
                                more_arg = more_arg[
                                    0 : COLS
                                    - x
                                    - more_posun
                                    - posun
                                    - len(function[_func][3][arg_num])
                                    - _increment
                                    - 3
                                ]
                            if more_posun < 0:
                                more_posun = 0
                            if isinstance(function[_func][3][arg_num], dict):
                                string(
                                    y - 1,
                                    x
                                    + posun
                                    + len(function[_func][3][arg_num][main_arg])
                                    + more_posun,
                                    more_arg,
                                )
                            else:
                                string(
                                    y - 1,
                                    x
                                    + posun
                                    + len(function[_func][3][arg_num])
                                    + more_posun,
                                    more_arg,
                                )
                            string(y, x + len(vstup), "")
                        except IndexError:
                            pass
                    if ikey == "" and not inp:
                        inp = True
                        vstup += ikey
                        # curses.nocbreak()
                        # stdscr.keypad(False)
                        curses.echo()
                        string(y + 1, x, ikey)
                    key = stdscr.getkey()
                    if inp:
                        if not key == "\n":
                            if key == "\x01":
                                select_all = True
                                curses.init_pair(
                                    1, curses.COLOR_BLACK, curses.COLOR_WHITE
                                )
                            elif key == "\x16":
                                win32clipboard.OpenClipboard()
                                data = win32clipboard.GetClipboardData().replace(
                                    "\n", " "
                                )
                                win32clipboard.CloseClipboard()
                                vstup = vstup + data
                            elif key == "\x08":
                                if _func is not None and function[_func] == "help":
                                    vstup = ikey + _func[:-1]
                                    _func = None
                                elif select_all:
                                    vstup = ikey
                                    curses.init_pair(
                                        1, curses.COLOR_WHITE, curses.COLOR_BLACK
                                    )
                                    select_all = False
                                else:
                                    vstup = vstup[0:-1]
                                if vstup == "":
                                    vstup = ikey
                                string(y, x + len(vstup), "")
                            elif key == "KEY_BTAB":
                                if _func == "help" and vstup[-1] in ["\t", " "]:
                                    vstup = vstup[:-1]
                                    while vstup[-1] == " ":
                                        vstup = vstup[:-1]
                            elif key == "KEY_A2":
                                pass
                            elif key == "KEY_B3":
                                if _func == "help":
                                    vstup += "\t"
                                    key = "\t"
                            elif key == "KEY_B1":
                                if _func == "help" and vstup[-1] in ["\t", " "]:
                                    vstup = vstup[:-1]
                                    while vstup[-1] == " ":
                                        vstup = vstup[:-1]
                                    key = "KEY_BTAB"
                            elif key == "KEY_C2":
                                pass
                            elif key.startswith("KEY_F("):
                                if key.endswith(")"):
                                    f_number = key[-2]
                            else:
                                if select_all:
                                    curses.init_pair(
                                        1, curses.COLOR_WHITE, curses.COLOR_BLACK
                                    )
                                    select_all = False
                                vstup += key
                        else:
                            vstup = vstup.strip() + " "
                    if key == ikey:
                        if vstup == ikey * 2:
                            inp = False
                            konecna = True
                        elif vstup == "":
                            inp = True
                            vstup += ikey
                            # curses.nocbreak()
                            # stdscr.keypad(False)
                            curses.echo()
                            if border:
                                string(y + 1, x, ikey)
                            else:
                                string(y, x, ikey)
                    if key == "\n" and _func is not None:
                        if function[_func] == "help":
                            vstup = ikey + __func_to_use + " "
                        else:
                            konecna = True
                            inp = False
                            curses.cbreak()
                            stdscr.keypad(True)
                            curses.noecho()
                        if border:
                            string(y + 1, x, int(COLS - 1 - x) * "_")
                            string(y - 1, x, COLS * "_")
                        else:
                            string(y, x, int(COLS - 1 - x) * " ")
                            string(y - 1, x, COLS * " ")
                    if konecna:
                        limit -= 1
                        if not ikey == "":
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
                                    if func == vstup.split(" ")[0]:
                                        if function[func][1][0] == "args":
                                            func_args = vstup[len(func) :].split(" ")
                                            func_args = list(
                                                filter(("").__ne__, func_args)
                                            )
                                        command = function[func][0]
                                        to_func = True
                                        try:
                                            ids[func]
                                        except KeyError:
                                            ids[func] = get_id()
                                elif (
                                    func == vstup[function[func][0] : function[func][1]]
                                ):
                                    to_func = True
                                    if callable(function[func][2]):
                                        command = function[func][2]
                                    elif len(function[func][2]) == 2:
                                        if function[func][2][1][0] == "args":
                                            try:
                                                func_args = vstup.split(" ", 1)[
                                                    1
                                                ].split(" ")
                                            except IndexError:
                                                if nof:
                                                    func_args = vstup
                                                else:
                                                    raise ValueError
                                            func_args = list(
                                                filter(("").__ne__, func_args)
                                            )
                                        else:
                                            func_args = function[func][2][1]
                                            if not isinstance(func_args, list):
                                                raise ValueError()
                                        command = function[func][2][0]
                                    else:
                                        command = function[func][2]
                                    try:
                                        ids[func]
                                    except KeyError:
                                        ids[func] = get_id()
                            else:
                                if func == vstup:
                                    try:
                                        ids[func]
                                    except KeyError:
                                        ids[func] = get_id()
                                    to_func = True
                                    command = function[func]

                            if to_func:
                                if command == "break":
                                    end = True
                                    break
                                if command == "help":
                                    continue
                                if command == "reset":
                                    try:
                                        self.reset(
                                            history[
                                                history_number - 2 - history_in_row * 2
                                            ]
                                        )
                                        history_in_row += 1
                                        func_reset = True
                                    except KeyError:
                                        pass
                                else:
                                    if last_command == command:
                                        self.restore(last_command_history[ids[func]])
                                    history_in_row = 0
                                    in_func = True
                                    current_id = func
                                    if func_args is not None:
                                        command(*func_args)
                                    else:
                                        command()
                                    last_command = command
                                    in_func = False
                                self.add_history(window)
                        func_args = None
                        vstup = ""
                    if limit == 0:
                        break
                    if end:
                        break
                self.add_history(window)
        return self

    def add(self, *args):
        for times, arg in enumerate(args):
            times += self.length
            setattr(self, f"component_{times}", arg())


class component(builder):
    def __init__(
        self,
        content: list[str],
        y: int,
        x: int,
        height: int | None = None,
        width: int | None = None,
        border: bool = False,
    ):
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
                self.content.append("")
        elif len(self.content) < self.height - 2 and self.border:
            for i in range(self.height - len(self.content) - 2):
                self.content.append("")

    def __call__(self) -> dict:
        window = {"type": "component"}
        if self.border:
            window[self.y] = [self.x, (self.width + 2) * "_"]
            window[self.y + self.height + 1] = [self.x, "|" + (self.width) * "_" + "|"]
        number = 0
        times = 1 if self.border else 0
        for times in range(self.y + times, self.height + self.y + times):
            if not self.border:
                window[self.y + number] = [
                    self.x,
                    self.content[number]
                    + (self.width - len(self.content[number])) * " ",
                ]
            if self.border:
                window[self.y + number + 1] = [
                    self.x,
                    "|"
                    + self.content[number]
                    + (self.width - len(self.content[number])) * " "
                    + "|",
                ]
            number += 1
        return window


class cinput(builder):
    def __init__(
        self,
        y: int,
        x: int,
        key: str,
        function: dict[
            str,
            str
            | list[
                int, int, list[callable, list[any]], list[str], list[str | list[str]]
            ],
        ],
        width: None | int = None,
        border: bool = False,
        limit: int = -1,
        nof: bool = False,
        help: None | str = "",
    ):
        self.y = y
        self.x = x
        self.width = width
        self.border = border
        self.key = key
        self.function = function
        self.limit = limit
        self.nof = nof
        self.help = help

    def __call__(self) -> dict:
        window = {
            "type": "cinput",
            "key": self.key,
            "x": self.x + 1 if self.border else self.x,
            "y": self.y,
            "border": self.border,
            "function": self.function,
            "width": self.width,
            "limit": self.limit,
            "nof": self.nof,
            "help": self.help,
        }
        width = self.width
        if self.border:
            if width is None:
                window[self.y] = [self.x, (COLS - self.x) * "_"]
                window[self.y + 1] = [self.x, "|" + (COLS - 2 - self.x) * "_" + "|"]
            else:
                window[self.y] = [self.x, (width + 2) * "_"]
                window[self.y + 1] = [self.x, "|" + (width) * "_" + "|"]
        return window


def search_engine(query, data) -> None | list[str]:
    if query in ["", "\t"]:
        return data

    query_words = query.lower().split()

    results = []
    for item in data:
        words = item.lower().replace('"', "").replace("'", "").split()
        match = True
        for query_word in query_words:
            word_matched = False
            for word in words:
                distance = Levenshtein.distance(query_word, word)
                if distance <= 1:
                    word_matched = True
                    break
            if not word_matched:
                match = False
                break
        if match:
            results.append(item)
            break

    if results:
        return results
    else:
        return None


def search_engine_double(query, data) -> None | list[str]:
    if query in ["", "\t"]:
        _data = []
        for i in data:
            for times, j in enumerate(i):
                if times == 0:
                    _data.append(j)
        return _data

    query_words = query.lower().split()

    results = []
    for item in data:
        for text in item:
            words = text.lower().replace('"', "").replace("'", "").split()
            match = True
            for query_word in query_words:
                word_matched = False
                for word in words:
                    distance = Levenshtein.distance(query_word, word)
                    if distance <= 1:
                        word_matched = True
                        break
                if not word_matched:
                    match = False
                    break
            if match:
                results.append(text)
                break

    if results:
        return results
    else:
        return None
