from Scanner import *

OP = 0
R1 = 1
VR1 = 2
PR1 = 3
NU1 = 4
R2 = 5
VR2 = 6
PR2 = 7
NU2 = 8
R3 = 9
VR3 = 10
PR3 = 11
NU3 = 12
IDX = 13


class IntermediateRepresentation:
    def __init__(self):
        # position 0 for op code, 1 for sr1, 5 for sr2, 9 for sr3
        self.ir = [None] * 14
        self.next = None
        self.prev = None

    def output(self):
        opcode = "" if self.ir[OP] is None else self.ir[OP]
        oprand1 = "" if self.ir[R1] is None else str(self.ir[R1])
        oprand2 = "" if self.ir[R2] is None else str(self.ir[R2])
        oprand3 = "" if self.ir[R3] is None else str(self.ir[R3])
        if opcode == "output" or opcode == "loadI":
            oprand1 = "" if oprand1 is "" else "val " + oprand1
            oprand2 = "" if oprand2 is "" else "sr" + oprand2
            oprand3 = "" if oprand3 is "" else "sr" + oprand3
        else:
            oprand1 = "" if oprand1 is "" else "sr" + oprand1
            oprand2 = "" if oprand2 is "" else "sr" + oprand2
            oprand3 = "" if oprand3 is "" else "sr" + oprand3
        res = "{} [ {} ], [ {} ], [ {} ]\n".format(opcode, oprand1, oprand2, oprand3)
        sys.stdout.write(res)

    def print_ir(self):
        print("OPCODE: {},\t SR1: {},\t VR1: {},\t PR1: {},\t NU1: {},\t "
              "SR2: {},\t VR2: {},\t PR2: {},\t NU2: {},\t "
              "SR3: {},\t VR3: {},\t PR3: {},\t NU3: {}"
              .format(self.ir[OP], self.ir[R1], self.ir[VR1], self.ir[PR1], self.ir[NU1],
                      self.ir[R2], self.ir[VR2], self.ir[PR2], self.ir[NU2],
                      self.ir[R3], self.ir[VR3], self.ir[PR3], self.ir[NU3]))


class Parser:
    def __init__(self, _scanner, _ir):
        self.scanner = _scanner
        self.error = 0
        self.ir = _ir
        # count number of ir
        self.count = 0
        self.maxSR = 0
        self.tail = None
        self.records = []

    def parse_line(self):
        tokens = self.scanner.token_line()
        res = []
        # print(tokens)
        if tokens:
            word = tokens[0]
            if word[2] == MEMOP_TYPE:
                res = self.finish_memop(tokens)

            elif word[2] == ARITHOP_TYPE:
                res = self.finish_arithop(tokens)

            elif word[2] == LOADI_TYPE:
                res = self.finish_loadI(tokens)

            elif word[2] == OUTPUT_TYPE:
                # print(tokens)
                res = self.finish_output(tokens)
            elif word[2] == NOP_TYPE:
                res = self.finish_nop(tokens)
            else:
                # print(tokens)
                self.start_err(tokens[0])
        if res:
            new_ir = IntermediateRepresentation()
            # print(tokens[0][1], tokens[0][2])
            new_ir.ir[OP] = tokens[0][1]
            # print(tokens[0][1])
            # print(res)
            if tokens[0][2] == MEMOP_TYPE:
                new_ir.ir[R1] = int(res[0]) if res else None
                new_ir.ir[R3] = int(res[2]) if len(res) > 2 else None
                self.maxSR = max(new_ir.ir[R1], new_ir.ir[R3], self.maxSR)
            elif tokens[0][2] == LOADI_TYPE:
                new_ir.ir[R1] = int(res[0]) if res else None
                new_ir.ir[R3] = int(res[2]) if len(res) > 2 else None
                self.maxSR = max(new_ir.ir[R1], new_ir.ir[R3], self.maxSR)
            elif tokens[0][2] == ARITHOP_TYPE:
                new_ir.ir[R1] = int(res[0]) if res else None
                new_ir.ir[R2] = int(res[2]) if len(res) > 2 else None
                new_ir.ir[R3] = int(res[4]) if len(res) > 4 else None
                self.maxSR = max(new_ir.ir[R1], new_ir.ir[R2], new_ir.ir[R3], self.maxSR)
            elif tokens[0][2] == OUTPUT_TYPE:
                # print(res)
                new_ir.ir[R1] = int(res[0]) if res else None
                self.maxSR = max(new_ir.ir[R1], self.maxSR)
            # new_ir.ir[IDX] = 0 if not self.tail.ir[IDX] else self.tail.ir[IDX] + 1
            # new_ir.prev = self.tail
            # self.tail.next = new_ir
            # self.tail = self.tail.next
            if not self.tail:
                self.tail = new_ir
            new_ir.next = self.ir.next
            new_ir.prev = self.ir
            if self.ir.next:
                self.ir.next.prev = new_ir
            self.ir.next = new_ir
            self.count += 1
        return res

    def finish_memop(self, tokens):
        # memop register into register
        grammer = [
            ("REG", "source register"),
            ("INTO", "'=>'"),
            ("REG", "target register")
        ]
        token_len = len(tokens)
        # print(tokens)
        if token_len > len(grammer) + 1:
            self.start_err(tokens[len(grammer)])
            return []
        elif token_len < len(grammer) + 1:
            # print("debug 1")
            self.missing_err(tokens[0], grammer[token_len - 1][1])
            return []
        result = []
        # print(tokens)
        for i in range(1, token_len):
            # print(types[tokens[i][2]])
            if types[tokens[i][2]] != grammer[i - 1][0]:
                # print(tokens[i][2], types(tokens[i][2]), grammer[i - 1][0])
                # print("debug 2")
                self.missing_err(tokens[0], grammer[i - 1][1])
                return []
            else:
                result.append(tokens[i][1])
                # print(result)
        return result

    def finish_loadI(self, tokens):
        grammer = [
            ('CONSTANT', 'constant'),
            ('INTO', "'=>'"),
            ('REG', 'target register')
        ]
        token_len = len(tokens)
        if token_len > len(grammer) + 1:
            self.start_err(tokens[len(grammer)])
            return []
        elif token_len < len(grammer) + 1:
            self.missing_err(tokens[0], grammer[token_len - 1][1])
            return []
        result = []
        for i in range(1, token_len):
            if types[tokens[i][2]] != grammer[i - 1][0]:
                self.missing_err(tokens[0], grammer[i - 1][1])
                return []
            else:
                result.append(tokens[i][1])
        return result

    def finish_arithop(self, tokens):
        grammer = [
            ('REG', 'first source register'),
            ('COMMA', "','"),
            ('REG', 'second source register'),
            ('INTO', "'=>'"),
            ('REG', 'target register')
        ]
        token_len = len(tokens)
        if token_len > len(grammer) + 1:
            self.start_err(tokens[len(grammer)])
            return []
        elif token_len < len(grammer) + 1:
            self.missing_err(tokens[0], grammer[token_len - 1][1])
            return []
        result = []
        for i in range(1, token_len):
            if types[tokens[i][2]] != grammer[i - 1][0]:
                self.missing_err(tokens[0], grammer[i - 1][1])
                return []
            else:
                result.append(tokens[i][1])
        return result

    def finish_output(self, tokens):
        grammer = [
            ('CONSTANT', 'constant')
        ]
        token_len = len(tokens)
        if token_len > len(grammer) + 1:
            self.start_err(tokens[len(grammer)])
            return []
        elif token_len < len(grammer) + 1:
            self.missing_err(tokens[0], grammer[token_len - 1][1])
            return []
        result = []
        for i in range(1, token_len):
            # print(tokens[i])
            if types[tokens[i][2]] != grammer[i - 1][0]:
                self.missing_err(tokens[0], grammer[i - 1][1])
                return []
            else:
                result.append(tokens[i][1])
        return result

    def finish_nop(self, tokens):
        if len(tokens) > 1:
            self.start_err(tokens[1])
            return []
        result = [tokens[0][1]]
        return result

    def start_err(self, token):
        print(token)
        res = "ERROR: {}: Operation starts with an invalid opcode: \'{}\'.\n"\
            .format(token[0], token[1])
        self.error += 1
        sys.stderr.write(res)

    def missing_err(self, token, rule):
        res = "Missing {} in {} on line {}.\n".format(rule, token[1], token[0])
        self.error += 1
        sys.stderr.write(res)


def renameReg(ir, maxSR, irLen):
    VRname = 0
    SRToVR = [None for _ in range(maxSR)]
    lu = [float("inf") for _ in range(maxSR)]
    cur_IR = ir

    max_live = 0
    max_vr = 0
    records = []

    while cur_IR:
        # for each oprand O that OP defines
        cur = cur_IR.ir
        cur[IDX] = irLen
        records.append(cur_IR)
        if cur[R3] is not None and cur[OP] != STORE:
            sr = cur[R3]
            if SRToVR[sr] is None:
                SRToVR[sr] = VRname
                VRname += 1
            cur[VR3] = SRToVR[sr]
            cur[NU3] = lu[sr]
            SRToVR[sr] = None
            lu[sr] = float("inf")

        if cur[R1] is not None:
            sr = cur[R1]
            if not (cur[OP] == LOADI or cur[OP] == OUTPUT):
                # print(cur[OP])
                if SRToVR[sr] is None:
                    SRToVR[sr] = VRname
                    VRname += 1
                cur[VR1] = SRToVR[sr]
                cur[NU1] = lu[sr]
                lu[sr] = irLen
        if cur[R2] is not None:
            sr = cur[R2]
            if not SRToVR[sr]:
                SRToVR[sr] = VRname
                VRname += 1
            cur[VR2] = SRToVR[sr]
            cur[NU2] = lu[sr]
            lu[sr] = irLen
        if cur[R3] is not None and cur[OP] == STORE:
            sr = cur[R3]
            if not SRToVR[sr]:
                SRToVR[sr] = VRname
                VRname += 1
            cur[VR3] = SRToVR[sr]
            cur[NU3] = lu[sr]
            lu[sr] = irLen
        irLen -= 1
        cur_IR = cur_IR.next
        cur_live = len([sr for sr in SRToVR if sr is not None])
        max_live = max(max_live, cur_live)
        max_vr = max(max_vr, VRname)
    return records, max_live, max_vr - 1
