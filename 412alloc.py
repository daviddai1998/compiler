import sys
import os.path
from Scanner import *
from Allocator import *
from Parser import *
args = sys.argv

help_message = "COMP 412, Fall 2018 Front End (lab 2)\n" + \
               "Command Syntax:\n" + \
               "	./421alloc [flags] filename\n" + \
               "Required arguments:\n" + \
               "	filename  is the pathname (absolute or relative) to the input file\n" + \
               "Optional flags:" + \
               "	-h	 prints this message\n" + \
               "	-x	 rename the registers\n" + \
               "	k    This command will be used to invoke register allocation " \
               "for k registers on the input block contained in <file name>. For lab2, 3 <= k <= 64\n"


def main():
    # flags = set()
    if len(args) <= 1:
        sys.stderr.write("ERROR: Please provide the flag and the filename.\n")
    else:
        flag = args[1]
        # print(str(flag) + "\n")
        if flag == "-x":
            filename = args[2]
            rename(filename)
        elif flag == "-h":
            sys.stderr.write(help_message)
        elif flag:
            k = int(flag)
            filename = args[2]
            allocate(filename, k)


def rename(fn):
    f = ReadFile(fn)
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
        if curIR[0] == OUTPUT:
            sys.stdout.write("%s %d\n" % (instructions[curIR[OP]], curIR[R1]))
        elif curIR[0] == LOADI:
            sys.stdout.write("%s %d => r%d\n" % (instructions[curIR[OP]], curIR[R1], curIR[VR3]))
        elif curIR[0] == NOP:
            sys.stdout.write("%s \n" % (instructions[curIR[OP]]))
        elif curIR[0] == LOAD or curIR[0] == STORE:
            sys.stdout.write("%s r%d => r%d\n" % (instructions[curIR[OP]], curIR[VR1], curIR[VR3]))
        elif curIR[0] == LSHIFT or curIR[0] == RSHIFT \
                or curIR[0] == ADD or curIR[0] == SUB or curIR[0] == MULT:
            sys.stdout.write("%s r%d, r%d => r%d\n" % (instructions[curIR[OP]], curIR[VR1], curIR[VR2], curIR[VR3]))
        head = head.prev


def allocate(fn, k):
    f = ReadFile(fn)
    scanner = Scanner(f)
    ir = IntermediateRepresentation()
    parser = Parser(scanner, ir)
    while True:
        if parser.scanner.stop_flag:
            break
        parser.parse_line()

    records, maxlive, maxVR = renameReg(ir.next, parser.maxSR + 1, parser.count - 1)
    records = list(reversed(records))
    # print(maxlive)
    allocator = Allocator(records, maxlive, maxVR, k)
    # print(allocator.maxPR)
    allocator.run()


if __name__ == '__main__':
    main()
