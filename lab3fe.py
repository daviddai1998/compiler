from Allocator import *
from Parser import *
from Scheduler import *


def schedule():
    f = ReadFile("test.i")
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
    print(scheduler.dependency)
    ins = scheduler.instruction_schedule()
    print(ins)


if __name__ == '__main__':
    schedule()
