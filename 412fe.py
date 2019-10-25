import sys
import os.path
from Scanner import *
from Parser import *
args = sys.argv


help_message = "COMP 412, Fall 2018 Front End (lab 1)\n" + \
               "Command Syntax:\n" + \
               "	./421fe [flags] filename\n" + \
               "Required arguments:\n" + \
               "	filename  is the pathname (absolute or relative) to the input file\n" + \
               "Optional flags:" + \
               "	-h	 prints this message\n" + \
               "	-s	 prints tokens in token stream\n" + \
               "	-p	 invokes parser and reports on success or failure\n" + \
               "	-r	 prints human readable version of parser's IR\n"


def main():
    flags = set()
    if len(args) <= 1:
        sys.stderr.write("ERROR: Please provide the flag and the filename.\n" + help_message)
    else:
        for i in range(1, len(args)):
            arg = args[i]
            if arg[0] == '-':
                if arg[1]:
                    flags.add(arg[1])
                else:
                    sys.stderr.write("No flags provided after '-'.\n" + help_message)
                    return
            else:
                break
        if not flags:
            # if no flags, view as -p
            if len(args) > len(flags) + 2:
                sys.stderr.write("Error: Multiple file given.\n")
                return
            else:
                filename = args[1]
                if os.path.isfile(filename):
                    parse(filename)
                else:
                    sys.stderr.write("Error: The file does not exist.\n")
                    return
        elif 'h' in flags:
            sys.stderr.write(help_message)
        else:
            # code, flag, filename
            if len(args) > len(flags) + 2:
                sys.stderr.write("Error: Multiple file given.\n")
            else:
                filename = args[len(flags) + 1]
                if not os.path.isfile(filename):
                    sys.stderr.write("Error: The file does not exist.\n")
                else:
                    if 'r' in flags:
                        read(filename)
                    elif 'p' in flags:
                        parse(filename)
                    elif 's' in flags:
                        scan(filename)
                    else:
                        sys.stderr.write("Flag given is invalid.\n" + help_message)


def parse(file):
    f = ReadFile(file)
    scanner = Scanner(f)
    ir = IntermediateRepresentation()
    parser = Parser(scanner, ir)
    count = 0
    while True:
        if parser.scanner.stop_flag:
            break
        sentence = parser.parse_line()
        if sentence:
            count += 1

    errors = parser.error + parser.scanner.err_count
    if errors > 0:
        string = "Parser found {} syntax errors in {} lines of input.\n"
        sys.stdout.write(string.format(errors, scanner.line))
    else:
        string = "Parse succeeded, finding {} ILOC operations.\n"
        sys.stdout.write(string.format(count))


def scan(file):
    f = ReadFile(file)
    scanner = Scanner(f)
    while True:
        token_data = scanner.next_token()
        # print(token_data)
        if token_data:
            print_token(token_data)

            if token_data[2] == ENDFILE_TYPE:
                break


def read(file):
    # filename = sys.argv[1]
    f = ReadFile(file)
    scanner = Scanner(f)
    ir = IntermediateRepresentation()
    parser = Parser(scanner, ir)
    while True:
        if parser.scanner.stop_flag:
            break
        parser.parse_line()

    errors = parser.error + parser.scanner.err_count
    if errors > 0:
        string = "Due syntax errors, run terminates.\n"
        sys.stderr.write(string)
        return
    else:
        ir = parser.tail
        head = ir
        while head.prev:
            head.output()
            head = head.prev
        # ir = ir.next
        # head = ir
        # while head.next:
        #     head = head.next
        #
        # while head.prev:
        #     head.output()
        #     head = head.prev


def rename(file):
    f = ReadFile(file)
    scanner = Scanner(f)
    ir = IntermediateRepresentation()
    parser = Parser(scanner, ir)
    while True:
        if parser.scanner.stop_flag:
            break
        parser.parse_line()

    renameReg(ir.next, parser.maxSR + 1, parser.count - 1)
    # print(parser.maxSR + 1, parser.count)
    ir = ir.next
    head = ir
    while head.next:
        head = head.next

    while head.prev:
        curIR = head.ir
        if curIR[0] == "output":
            sys.stdout.write("%s %d\n" % (curIR[OP], curIR[R1]))
        elif curIR[0] == "loadI":
            sys.stdout.write("%s %d => r%d\n" % (curIR[OP], curIR[R1], curIR[VR3]))
        elif curIR[0] == "nop":
            sys.stdout.write("%s \n" % (curIR[OP]))
        elif curIR[0] == "load" or curIR[0] == "store":
            sys.stdout.write("%s r%d => r%d\n" % (curIR[OP], curIR[VR1], curIR[VR3]))
        elif curIR[0] == "lshift" or curIR[0] == "rshift" or curIR[0] == "add" or curIR[0] == "sub" or curIR[0] == "mult":
            sys.stdout.write("%s r%d, r%d => r%d\n" % (curIR[OP], curIR[VR1], curIR[VR2], curIR[VR3]))
        head = head.prev


if __name__ == '__main__':
    main()
    # rename("lab1/cc1.i")
