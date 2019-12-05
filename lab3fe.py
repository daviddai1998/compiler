from Allocator import *
from Parser import *
from Scheduler import *
import sys
args = sys.argv


help_message = "COMP 412, Fall 2018 Front End (lab 3)\n" + \
               "Command Syntax:\n" + \
               "	./421alloc [flags] filename\n" + \
               "Required arguments:\n" + \
               "	filename  is the pathname (absolute or relative) to the input file\n" + \
               "Optional flags:" + \
               "	-h	 prints this message\n" + \
               "for k registers on the input block contained in <file name>. For lab2, 3 <= k <= 64\n"


def main():
    # flags = set()
    if len(args) <= 1:
        sys.stderr.write("ERROR: Please provide the flag and the filename.\n")
    else:
        flag = args[1]
        # print(str(flag) + "\n")
        if flag == "-h":
            sys.stderr.write(help_message)
        elif flag:
            filename = flag
            schedule(filename)


def get_print(op, ir):
    out = ""
    if op[0] == -1:
        out = "nop"
    elif op[1] == OUTPUT:
        out = "{} {}".format(instructions[ir[OP]], ir[R1])
    elif op[1] == LOADI:
        out = "{} {} => r{}".format(instructions[ir[OP]], ir[R1], ir[VR3])
    elif op[1] == LOAD or op[1] == STORE:
        out = "{} r{} => r{}".format(instructions[ir[OP]], ir[VR1], ir[VR3])
    elif op[1] == LSHIFT or op[1] == RSHIFT \
            or op[1] == ADD or op[1] == SUB or op[1] == MULT:
        out = "{} r{}, r{} => r{}".format(instructions[ir[OP]], ir[VR1], ir[VR2], ir[VR3])
    return out


def schedule(filename):
    f = ReadFile(filename)
    scanner = Scanner(f)
    ir = IntermediateRepresentation()
    parser = Parser(scanner, ir)
    while True:
        if parser.scanner.stop_flag:
            break
        parser.parse_line()

    records, maxlive, maxVR = renameReg(ir.next, parser.maxSR + 1, parser.count - 1)
    records = list(reversed(records))

    scheduler = Scheduler(records)
    scheduler.compute_priority()
    # print(scheduler.dependency)
    ins, debug = scheduler.instruction_schedule()
    # print(debug)
    ir_collection = scheduler.IR
    for s1, s2 in ins:
        idx1 = s1[0] - 1
        idx2 = s2[0] - 1
        out1 = get_print(s1, ir_collection[idx1].ir)
        out2 = get_print(s2, ir_collection[idx2].ir)
        sys.stdout.write('[' + out1 + '; ' + out2 + ']\n')


if __name__ == '__main__':
    main()
