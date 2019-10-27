from Parser import *
# noinspection PyTypeChecker,PyStringFormat


class Allocator:
    def __init__(self, ir, max_live, max_vr, k):
        self.ir = ir  # A List of IRs
        self.k = k
        self.max_live = max_live
        self.maxVR = max_vr + 1
        self.memory_alloc = 32768
        self.maxPR = k if self.max_live <= k else k - 1
        self.VRToPR = [None for _ in range(self.maxVR)]
        self.VRToMem = [None for _ in range(self.maxVR)]
        self.VRToVal = [None for _ in range(self.maxVR)]
        self.clean = [False for _ in range(self.maxVR)]
        self.spilled = [False for _ in range(self.maxVR)]
        self.rematerial = [None for _ in range(self.maxVR)]

        self.PRToVR = [None for _ in range(self.maxPR)]
        self.PRNU = [float("inf") for _ in range(self.maxPR)]
        self.stack = [i for i in range(self.maxPR)]
        self.mark = None

    def run(self):
        for i in range(len(self.ir)):
            r = self.ir[i]
            # print("=================OPERATION {}=================".format(i))
            self.allocation(r)

    def getAPR(self, vr, nu):
        if self.VRToPR[vr] is not None:
            pr = self.VRToPR[vr]
            self.PRNU[pr] = nu
            return pr

        if self.stack:
            pr = self.stack.pop(0)
        else:
            pr = self.spill()
            clean_pr, clean_nu = self.max_cleanNU()
            rematerial_pr, remterial_nu = self.max_rematerialNU()
            if nu - max(clean_nu, remterial_nu) < 5:
                if clean_nu - remterial_nu < 3:
                    pr = rematerial_pr
                else:
                    pr = clean_pr

        if self.rematerial[vr] is not None:
            loadI_ir = self.rematerial[vr]
            sys.stdout.write("loadI {} => r{} \n".format(loadI_ir[R1], pr))

        self.VRToPR[vr] = pr
        self.PRToVR[pr] = vr
        self.PRNU[pr] = nu
        return pr

    def freeAPR(self, pr):
        vr = self.PRToVR[pr]
        if vr:
            self.VRToPR[vr] = None
        self.PRToVR[pr] = None
        self.PRNU[pr] = float("inf")

    def max_cleanNU(self):
        clean_pr = -1
        max_nu = -1
        for vr in range(self.maxVR):
            if self.clean[vr] is True:
                pr = self.VRToPR[vr]
                if pr == self.mark:
                    continue
                if self.PRNU[pr] > max_nu and self.PRNU[pr] != float("inf"):
                    max_nu = self.PRNU[pr]
                    clean_pr = pr
        return clean_pr, max_nu

    def max_rematerialNU(self):
        rematerial_pr = -1
        max_nu = -1
        for vr in range(self.maxVR):
            if self.rematerial[vr] is not None:
                pr = self.VRToPR[vr]
                if pr == self.mark:
                    continue
                if self.PRNU[pr] > max_nu and self.PRNU[pr] != float("inf"):
                    max_nu = self.PRNU[pr]
                    rematerial_pr = pr
        return rematerial_pr, max_nu

    def spill(self):
        spill_pr = -1
        max_nu = -1
        for pr in range(self.maxPR):
            # print(pr, nu)
            if pr == self.mark:
                continue
            if self.PRNU[pr] > max_nu and self.PRNU[pr] != float("inf"):
                max_nu = self.PRNU[pr]
                spill_pr = pr

        spill_vr = self.PRToVR[spill_pr]

        # if the vr is dirty, just print out for now
        if self.rematerial[spill_vr] is None and not self.clean[spill_vr]:
            # spill_vr type may not be correctsss
            self.VRToMem[spill_vr] = self.memory_alloc
            # sys.stdout.write("// spill\n")
            sys.stdout.write('loadI %d => r%d \n' % (self.memory_alloc, len(self.PRToVR)))
            sys.stdout.write('store r%d => r%d \n' % (spill_pr, len(self.PRToVR)))
            # sys.stdout.write("// spill finished\n")
            self.clean[spill_vr] = True
            self.memory_alloc += 4

        self.VRToPR[spill_vr] = None
        self.spilled[spill_vr] = True
        return spill_pr

    def restore(self, vr, pr):
        if self.spilled[vr] and self.rematerial[vr] is None:
            sys.stdout.write('loadI %d => r%d\n' % (self.VRToMem[vr], pr))
            sys.stdout.write('load r%d => r%d\n' % (pr, pr))

    def allocation(self, record):
        ir = record.ir
        opcode = ir[OP]
        if opcode == LSHIFT or opcode == RSHIFT \
                or opcode == ADD or opcode == SUB or opcode == MULT:
            if self.VRToVal[ir[VR1]] is None or self.VRToVal[ir[VR2]] is None:
                self.VRToVal[ir[VR3]] = None
            else:
                if opcode == ADD:
                    self.VRToVal[ir[VR3]] = self.VRToVal[ir[VR1]] + self.VRToVal[ir[VR2]]
                elif opcode == SUB:
                    self.VRToVal[ir[VR3]] = self.VRToVal[ir[VR1]] - self.VRToVal[ir[VR2]]
                elif opcode == MULT:
                    self.VRToVal[ir[VR3]] = self.VRToVal[ir[VR1]] * self.VRToVal[ir[VR2]]
                elif opcode == LSHIFT:
                    self.VRToVal[ir[VR3]] = self.VRToVal[ir[VR1]] << self.VRToVal[ir[VR2]]
                elif opcode == RSHIFT:
                    self.VRToVal[ir[VR3]] = self.VRToVal[ir[VR1]] >> self.VRToVal[ir[VR2]]

            if self.VRToPR[ir[VR1]] is None:
                ir[PR1] = self.getAPR(ir[VR1], ir[NU1])
            else:
                ir[PR1] = self.VRToPR[ir[VR1]]
                self.PRNU[ir[PR1]] = ir[NU1]
            self.restore(ir[VR1], ir[PR1])

            self.mark = ir[PR1]

            if self.VRToPR[ir[VR2]] is None:
                ir[PR2] = self.getAPR(ir[VR2], ir[NU2])
            else:
                ir[PR2] = self.VRToPR[ir[VR2]]
                self.PRNU[ir[PR2]] = ir[NU2]
            self.restore(ir[VR2], ir[PR2])

            if ir[NU1] == float("inf"):
                self.freeAPR(ir[PR1])
                self.stack.insert(0, ir[PR1])

            if ir[NU2] == float("inf"):
                self.freeAPR(ir[PR2])
                self.stack.insert(0, ir[PR2])

            self.mark = None

            ir[PR3] = self.getAPR(ir[VR3], ir[NU3])
            if ir[NU3] == float("inf"):
                self.freeAPR(ir[PR3])
                self.stack.insert(0, ir[PR3])

        elif opcode == LOADI:
            # need to re-materialize
            self.rematerial[ir[VR3]] = ir
            self.VRToVal[ir[VR3]] = ir[R1]

        elif opcode == LOAD:
            if self.VRToPR[ir[VR1]] is None:
                ir[PR1] = self.getAPR(ir[VR1], ir[NU1])
            else:
                ir[PR1] = self.VRToPR[ir[VR1]]
                self.PRNU[ir[PR1]] = ir[NU1]
            self.restore(ir[VR1], ir[PR1])

            # print(ir, ir[NU1], ir[PR3])
            if ir[NU1] == float("inf"):
                self.freeAPR(ir[PR1])
                self.stack.insert(0, ir[PR1])
            # allocate PR for def
            ir[PR3] = self.getAPR(ir[VR3], ir[NU3])
            # print(ir[PR3])
            if ir[NU3] == float("inf"):
                self.freeAPR(ir[PR3])
                # print(ir[PR3])
                self.stack.insert(0, ir[PR3])

        elif opcode == STORE:
            if self.VRToPR[ir[VR1]] is None:
                ir[PR1] = self.getAPR(ir[VR1], ir[NU1])
            else:
                ir[PR1] = self.VRToPR[ir[VR1]]
                self.PRNU[ir[PR1]] = ir[NU1]
            self.restore(ir[VR1], ir[PR1])

            self.mark = ir[PR1]

            if self.VRToPR[ir[VR3]] is None:
                ir[PR3] = self.getAPR(ir[VR3], ir[NU3])
            else:
                ir[PR3] = self.VRToPR[ir[VR3]]
                self.PRNU[ir[PR3]] = ir[NU3]
            self.restore(ir[VR3], ir[PR3])

            self.mark = None
            self.rematerial[ir[VR3]] = None
            self.clean[ir[VR3]] = False

            if ir[NU1] == float("inf"):
                self.freeAPR(ir[PR1])
                self.stack.insert(0, ir[PR1])

            if ir[NU3] == float("inf"):
                self.freeAPR(ir[PR3])
                self.stack.insert(0, ir[PR3])

        if ir[0] == OUTPUT:
            sys.stdout.write("%s %d\n" % (instructions[ir[OP]], ir[R1]))
        elif ir[0] == NOP:
            sys.stdout.write("%s \n" % (instructions[ir[OP]]))
        elif ir[0] == LOAD or ir[0] == STORE:
            sys.stdout.write("%s r%d => r%d\n" % (instructions[ir[OP]], ir[PR1], ir[PR3]))
        elif ir[0] == LSHIFT or ir[0] == RSHIFT \
                or ir[0] == ADD or ir[0] == SUB or ir[0] == MULT:
            sys.stdout.write("%s r%d, r%d => r%d\n" % (instructions[ir[OP]], ir[PR1], ir[PR2], ir[PR3]))
