import sys

types = [
    'MEMOP',
    'ARITHOP',
    'LOADI',
    'NOP',
    'OUTPUT',
    'INTO',
    'COMMA',
    'CONSTANT',
    'REG',
    'ENDFILE'
]

instructions = [
    "load",     # 0
    "store",    # 1
    "loadI",    # 2
    "add",      # 3
    "sub",      # 4
    "mult",     # 5
    "lshift",   # 6
    "rshift",   # 7
    "output",   # 8
    "nop"       # 9
]

LOAD = 0
STORE = 1
LOADI = 2
ADD = 3
SUB = 4
MULT = 5
LSHIFT = 6
RSHIFT = 7
OUTPUT = 8
NOP = 9

NUMBERS = '01234856789'

MEMOP_TYPE = 0
ARITHOP_TYPE = 1
LOADI_TYPE = 2
NOP_TYPE = 3
OUTPUT_TYPE = 4
INTO_TYPE = 5
COMMA_TYPE = 6
CONSTANT_TYPE = 7
REGISTER_TYPE = 8
ENDFILE_TYPE = 9


class ReadFile:
    def __init__(self, name):
        self.f = open(name, 'r')
        self.buffer = ""
        self.ptr = 0

    def fill_buffer(self):
        self.buffer = self.f.read(4096)
        self.ptr = 0
        return

    def getchar(self):
        try:
            self.ptr += 1
            return self.buffer[self.ptr - 1]
        except IndexError:
            # reach the end of the buffer
            self.fill_buffer()
            try:
                self.ptr += 1
                return self.buffer[self.ptr - 1]
            except IndexError:
                return ""


class Scanner:
    def __init__(self, f):
        # takes in a readFile class
        self.file = f
        self.line = 1
        self.word = ""
        self.tokenLine = []
        self.last = None
        self.stop_flag = False
        self.err_flag = False
        self.err_count = 0

    def getchar(self):
        return self.file.getchar()

    def read_next_line(self):
        char = self.getchar()
        while char and char not in '\r\n':
            char = self.getchar()
        self.line += 1
        self.word = ""

    def token_line(self):
        self.tokenLine = []
        if self.last:
            self.tokenLine.append(self.last)
        thisLine = self.line
        while thisLine == self.line:
            if not self.stop_flag:
                t = self.next_token()
                # print(t)
                if t:
                    self.tokenLine.append(t)
            else:
                break
        if not self.err_flag:
            if self.tokenLine:
                if len(self.tokenLine) >= 2:
                    if self.tokenLine[-1][0] != self.tokenLine[0][0]:
                        self.last = self.tokenLine.pop()
                elif len(self.tokenLine) == 1:
                    self.last = self.tokenLine.pop()
                return self.tokenLine
        else:
            self.err_flag = False
            self.last = ""
            return []

    def next_token(self):
        if not self.word:
            char = self.getchar()
            if char:
                self.word += char
            else:
                # self.line -= 1
                self.stop_flag = True
                return self.line, None, ENDFILE_TYPE
        else:
            # if word has some characters
            char = self.word[-1]

        if char == ' ' or char == '\t':
            self.word = ""
            token = self.next_token()
            return token

        elif char == 's':
            next1 = self.getchar()
            self.word += next1

            if next1 == 't':
                if self.check_remaining("ore"):
                    if self.check_whitespace():
                        self.word = ""
                        return self.line, STORE, MEMOP_TYPE
                    else:
                        self.whitespace_err()
            elif next1 == 'u':
                if self.check_remaining("b"):
                    if self.check_whitespace():
                        self.word = ""
                        return self.line, SUB, ARITHOP_TYPE
                    else:
                        self.whitespace_err()
            else:
                self.valid_err(self.word)

        elif char == 'l':
            next1 = self.getchar()
            # print(next1)
            if next1:
                self.word += next1
                if next1 == 'o':
                    if self.check_remaining("ad"):
                        isLoadI = self.check_load()
                        if isLoadI:
                            if self.check_whitespace():
                                self.word = ""
                                return self.line, LOADI, LOADI_TYPE
                            else:
                                self.whitespace_err()
                        elif self.word[-1] == ' ' or self.word[-1] == '\t':
                            self.word = ""
                            return self.line, LOAD, MEMOP_TYPE
                        else:
                            self.whitespace_err()
                elif next1 == 's':
                    if self.check_remaining("hift"):
                        if self.check_whitespace():
                            self.word = ""
                            return self.line, LSHIFT, ARITHOP_TYPE
                        else:
                            self.whitespace_err()
            else:
                self.valid_err(self.word)

        elif char == 'r':
            next1 = self.getchar()

            if next1 == 's':
                if self.check_remaining("hift"):
                    if self.check_whitespace():
                        self.word = ""
                        return self.line, RSHIFT, ARITHOP_TYPE
                    else:
                        self.whitespace_err()

            elif next1 in NUMBERS:
                return self.line, str(self.scan_constant(next1)), REGISTER_TYPE

            else:
                self.valid_err(self.word)

        elif char == 'm':
            if self.check_remaining("ult"):
                if self.check_whitespace():
                    self.word = ""
                    return self.line, MULT, ARITHOP_TYPE
                else:
                    self.whitespace_err()

        elif char == 'a':
            if self.check_remaining("dd"):
                if self.check_whitespace():
                    self.word = ""
                    return self.line, ADD, ARITHOP_TYPE
                else:
                    self.whitespace_err()

        elif char == 'n':
            if self.check_remaining("op"):
                if self.check_whitespace():
                    self.word = ""
                    return self.line, NOP, NOP_TYPE
                else:
                    self.whitespace_err()

        elif char == 'o':
            if self.check_remaining("utput"):
                if self.check_whitespace():
                    self.word = ""
                    return self.line, OUTPUT, OUTPUT_TYPE
                else:
                    self.whitespace_err()

        elif char == '=':
            if self.check_remaining('>'):
                self.word = ""
                return self.line, None, INTO_TYPE

        elif char == ',':
            self.word = ""
            return self.line, None, COMMA_TYPE

        elif char == '/':
            self.check_comments()
            return self.next_token()

        elif char == '\n' or char == '\r':
            self.line += 1
            self.word = ""
            # print("zheli")
            return self.next_token()

        elif char in NUMBERS:
            return self.line, self.scan_constant(char), CONSTANT_TYPE

        # else:
        #     self.valid_err(self.word)

        self.word = ""

    def check_whitespace(self):
        char = self.getchar()
        self.word += char
        if char == ' ' or char == '\t':
            return True
        return False

    def check_comments(self):
        char = self.getchar()
        self.word += char

        if char == '/':
            # read rest of line
            self.read_next_line()
            self.word = ""
        else:
            # return error token
            self.valid_err(self.word)

    def scan_constant(self, start):
        num = int(start)
        constant = self.getchar()
        while constant in NUMBERS:
            if constant:
                num = num * 10 + int(constant)
                constant = self.getchar()
            else:
                break

        # store the number, may not need this
        self.word = constant
        return num

    def check_remaining(self, match):
        for ch in match:
            cur_char = self.getchar()
            self.word += cur_char
            if cur_char != ch:
                self.valid_err(self.word)
                return False
        return True

    def check_load(self):
        char = self.getchar()
        self.word += char
        if char != 'I':
            return False
        return True

    def valid_err(self, msg):
        res = "Lexical Error: Line {}: \"{}\" is not a valid word.\n".format(self.line, "".join(msg).strip())
        sys.stderr.write(res)
        self.err_flag = True
        self.err_count += 1
        self.read_next_line()

    def whitespace_err(self):
        res = "Lexical Error: Line {}: Op-codes must be followed by whitespace.\n".format(self.line)
        sys.stderr.write(res)
        self.err_flag = True
        self.err_count += 1
        self.read_next_line()


def token_str(token):
    string = ""
    if token[2] in [MEMOP_TYPE, LOADI_TYPE, ARITHOP_TYPE, OUTPUT_TYPE, NOP_TYPE]:
        # print(tok[1], tok[2])
        string = instructions[token[1]]
    elif token[2] == CONSTANT_TYPE:
        string = instructions[token[1]]
    elif token[2] == REGISTER_TYPE:
        string = "r" + str(token[1])
    elif token[2] == COMMA_TYPE:
        string = ","
    elif token[2] == INTO_TYPE:
        string = "=>"

    return string


def print_token(token):
    sys.stdout.write(str(token[0]) + ": < " + types[token[2]] + ", " + "\"" + token_str(token) + "\" >\n")
