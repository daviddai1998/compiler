import sys
import os.path
from Scanner import *
from Allocator import *
from Parser import *
args = sys.argv


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
        elif flag:
            k = int(flag)
            filename = args[2]
            allocate(filename, k)


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
        elif curIR[0] == "lshift" or curIR[0] == "rshift" \
                or curIR[0] == "add" or curIR[0] == "sub" or curIR[0] == "mult":
            sys.stdout.write("%s r%d, r%d => r%d\n" % (curIR[OP], curIR[VR1], curIR[VR2], curIR[VR3]))
        head = head.prev


def allocate(file, k):
    f = ReadFile(file)
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
