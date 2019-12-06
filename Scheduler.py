from Allocator import *
from collections import defaultdict, deque
import heapq
import copy


class Operation:
    def __init__(self, line, opcode):
        self.line = line
        self.opcode = opcode


class Scheduler:
    def __init__(self, ir):
        self.IR = ir
        self.is_serial = defaultdict(lambda: defaultdict(lambda: False))
        self.dependency = defaultdict(set)
        self.in_degree = defaultdict(int)
        self.reverse = defaultdict(set)
        self.priority = defaultdict(int)
        self.second = defaultdict(int)
        self.ready = []
        self.active = []
        self.latency = {
            LOAD: 5,
            STORE: 5,
            MULT: 3,
            LOADI: 1,
            ADD: 1,
            SUB: 1,
            LSHIFT: 1,
            RSHIFT: 1,
            OUTPUT: 1
        }
        self.build_dependency_graph()

    def build_dependency_graph(self):
        M = {}
        # pri_graph = defaultdict(set)
        VRToVal = {}
        # last_store = None
        # last_output = None

        last_store = []
        last_output = []
        all_loads = []

        for i in range(len(self.IR)):
            self.dependency[i + 1] = set()
            ir = self.IR[i].ir
            opcode = ir[OP]

            # nop jump to next iteration
            if opcode == NOP:
                continue

            if opcode == LOADI:
                const = ir[R1]
                vr = ir[VR3]
                VRToVal[vr] = int(const)

            if opcode == ADD:
                vr1 = ir[VR1]
                vr2 = ir[VR2]
                vr3 = ir[VR3]
                if vr1 in VRToVal and vr2 in VRToVal:
                    VRToVal[vr3] = VRToVal[vr1] + VRToVal[vr2]

            if opcode == SUB:
                vr1 = ir[VR1]
                vr2 = ir[VR2]
                vr3 = ir[VR3]
                if vr1 in VRToVal and vr2 in VRToVal:
                    VRToVal[vr3] = VRToVal[vr1] - VRToVal[vr2]

            if opcode == MULT:
                vr1 = ir[VR1]
                vr2 = ir[VR2]
                vr3 = ir[VR3]
                if vr1 in VRToVal and vr2 in VRToVal:
                    VRToVal[vr3] = VRToVal[vr1] * VRToVal[vr2]

            node = (ir, i + 1)

            if opcode not in {STORE, OUTPUT, NOP}:
                # print(instructions[opcode], i, ir[VR3])
                M[ir[VR3]] = node

            vr1 = ir[VR1]
            vr2 = ir[VR2]
            vr3 = ir[VR3]
            if vr1 is not None:
                # print(vr1, node[1], instructions[opcode], M)
                if M[vr1][1] not in self.dependency[node[1]]:
                    self.dependency[node[1]].add(M[vr1][1])
                    self.is_serial[node[1]][M[vr1][1]] = True
                    self.reverse[M[vr1][1]].add(node[1])
                    # pri_graph[node[1]].add((M[vr1][1], False))

            if vr2 is not None:
                if M[vr2][1] not in self.dependency[node[1]]:
                    self.dependency[node[1]].add(M[vr2][1])
                    self.is_serial[node[1]][M[vr2][1]] = True
                    self.reverse[M[vr2][1]].add(node[1])
                    # pri_graph[node[1]].add((M[vr2][1], False))

            if opcode == STORE:
                if vr3 is not None:
                    if M[vr3][1] not in self.dependency[node[1]]:
                        self.dependency[node[1]].add(M[vr3][1])
                        self.is_serial[node[1]][M[vr3][1]] = True
                        self.reverse[M[vr3][1]].add(node[1])
                        # pri_graph[node[1]].add((M[vr3][1], False))

            # # find store before output and load
            # if opcode == OUTPUT:
            #     if last_store is not None:
            #         if last_store not in self.dependency[node[1]]:
            #             self.dependency[node[1]].add(last_store)
            #             self.reverse[last_store].add(node[1])
            #
            # if opcode == LOAD:
            #     if last_store is not None:
            #         if last_store not in self.dependency[node[1]]:
            #             self.dependency[node[1]].add(last_store)
            #             self.reverse[last_store].add(node[1])
            #
            # # output serialization edge to most recent output
            # if opcode == OUTPUT:
            #     if last_output is not None:
            #         if last_output not in self.dependency[node[1]]:
            #             self.dependency[node[1]].add(last_output)
            #             self.reverse[last_output].add(node[1])

            if opcode == OUTPUT:
                output_val = ir[R1]
                for ls in list(reversed(last_store)):
                    cur_vr3 = self.IR[ls - 1].ir[VR3]
                    if cur_vr3 in VRToVal and int(VRToVal[cur_vr3]) != int(output_val):
                        continue
                    if ls not in self.dependency[node[1]]:
                        self.dependency[node[1]].add(ls)
                        # self.is_serial[node[1]][ls] = True
                        self.reverse[ls].add(node[1])
                        # break

            if opcode == LOAD:
                load_val = VRToVal[vr1] if vr1 in VRToVal else None
                for ls in list(reversed(last_store)):
                    cur_vr3 = self.IR[ls - 1].ir[VR3]
                    if load_val is not None and cur_vr3 in VRToVal and int(VRToVal[cur_vr3]) != int(load_val):
                        continue
                    if ls not in self.dependency[node[1]]:
                        self.dependency[node[1]].add(ls)
                        # self.is_serial[node[1]][ls] = True
                        self.reverse[ls].add(node[1])
                        # break

            if opcode == OUTPUT:
                for lo in list(reversed(last_output)):
                    if lo not in self.dependency[node[1]]:
                        self.dependency[node[1]].add(lo)
                        self.reverse[lo].add(node[1])
                        break

            # store seialization edges to the most recent store and output, and all previous load
            if opcode == STORE:
                store_val = VRToVal[vr3] if vr3 in VRToVal else None

                if last_store:
                    for ls in list(reversed(last_store)):
                        cur_vr3 = self.IR[ls - 1].ir[VR3]
                        if store_val is not None and cur_vr3 in VRToVal and int(VRToVal[cur_vr3]) != int(store_val):
                            continue
                        if ls not in self.dependency[node[1]]:
                            self.dependency[node[1]].add(ls)
                            self.reverse[ls].add(node[1])
                            # break

                if last_output:
                    for lo in list(reversed(last_output)):
                        cur_val = self.IR[lo - 1].ir[R1]
                        if store_val is not None and int(cur_val) != int(store_val):
                            continue
                        if lo not in self.dependency[node[1]]:
                            self.dependency[node[1]].add(lo)
                            self.reverse[lo].add(node[1])
                            # break
                # if last_store is not None:
                #     if last_store not in self.dependency[node[1]]:
                #         self.dependency[node[1]].add(last_store)
                #         self.reverse[last_store].add(node[1])
                #
                # if last_output is not None:
                #     if last_output not in self.dependency[node[1]]:
                #         self.dependency[node[1]].add(last_output)
                #         self.reverse[last_output].add(node[1])

                if all_loads:
                    for idx in all_loads:
                        cur_vr1 = self.IR[idx - 1].ir[VR1]
                        if store_val is not None and cur_vr1 in VRToVal and int(VRToVal[cur_vr1]) != int(store_val):
                            continue
                        if idx not in self.dependency[node[1]]:
                            self.dependency[node[1]].add(idx)
                            self.reverse[idx].add(node[1])

            if opcode == STORE:
                last_store.append(i + 1)

            if opcode == OUTPUT:
                last_output.append(i + 1)

            # if opcode == STORE:
            #     last_store = i + 1
            #
            # if opcode == OUTPUT:
            #     last_output = i + 1

            if opcode == LOAD:
                all_loads.append(i + 1)
        return

    def compute_priority(self):
        root = len(self.IR)
        queue = deque([root])
        root_op = self.IR[root - 1].ir[OP]
        self.priority[root] = self.latency[root_op]
        self.second[root] = 1
        while queue:
            node = queue.popleft()
            for nbr in self.dependency[node]:
                opcode = self.IR[nbr - 1].ir[OP]
                queue.append(nbr)
                self.second[nbr] = max(self.second[nbr], self.second[nbr] + 1)
                self.priority[nbr] = max(self.priority[nbr], self.priority[node] + self.latency[opcode])
        return

    def isExist(self, f, num_out):
        next_op = None
        ops = []
        while self.ready:
            # print(self.ready)
            # print(type(self.ready))
            node = heapq.heappop(self.ready)
            # print("--is exist--")
            # print(node[1])
            opcode = node[1][1]
            # print("line: ", node[1][0], instructions[opcode])
            if opcode in f:
                if opcode == OUTPUT and num_out > 0:
                    heapq.heappush(ops, node)
                else:
                    next_op = node
                    break
            else:
                heapq.heappush(ops, node)
        # print(self.ready, ops)
        self.ready = list(heapq.merge(ops, self.ready))
        return next_op

    def instruction_schedule(self):
        cycle = 1
        S = {}
        schedule = []
        debug = [[], []]
        # units = [{LOAD, STORE, LOADI, MULT, SUB, ADD, LSHIFT, RSHIFT, OUTPUT}]
        units = [{LOAD, STORE, LOADI, SUB, ADD, LSHIFT, RSHIFT, OUTPUT},
                 {LOADI, MULT, SUB, ADD, LSHIFT, RSHIFT, OUTPUT}]
        to_remove = []
        for k in self.dependency.keys():
            if not self.dependency[k]:
                opcode = self.IR[k - 1].ir[OP]
                to_remove.append(k)
                heapq.heappush(self.ready, (-self.priority[k], (k, opcode)))

        for r in to_remove:
            self.dependency.pop(r)

        while len(self.ready) > 0 or len(self.active) > 0:
            # print("------------CYCLE {}--------------".format(cycle))
            # print("Ready:", self.ready, "Active:", self.active)
            # print("-----debug1-----")
            num_output = 0
            op_pair = []
            for i in range(2):
                # the operation class
                flag = False
                f = units[i]
                node = self.isExist(f, num_output)
                if node is not None:
                    op = node[1]
                    if op[1] == OUTPUT:
                        num_output += 1
                    S[op[0]] = cycle
                    if op not in self.active:
                        self.active.append(op)
                        flag = True
                        op_pair.append((op[0], op[1]))
                        debug[i].append((op[0], op[1]))
                if not flag:
                    op_pair.append((-1, -1))
                    debug[i].append((-1, -1))
            schedule.append(tuple(op_pair))
            cycle += 1

            # print("-----active-----")
            # print(self.active, "Cycle:", cycle)
            new_active = copy.deepcopy(self.active)
            for idx in range(len(self.active)):
                op = self.active[idx]

                # print("-----S[{}]-----".format(instructions[op[1]]))
                # print("S[", op[0], "]: ", S[op[0]], "latency: ", self.latency[op[1]])
                if S[op[0]] + self.latency[op[1]] <= cycle:
                    # print("-------first-------")
                    new_active.remove(op)
                    for successor in self.reverse[op[0]]:
                        if op[0] in self.dependency[successor]:
                            self.dependency[successor].remove(op[0])
                        if not self.dependency[successor]:
                            # print("-----successor-----")
                            # print(successor)
                            self.dependency.pop(successor)
                            s_opcode = self.IR[successor - 1].ir[OP]
                            heapq.heappush(self.ready, (-self.priority[successor],
                                                        (successor, s_opcode)))
                    self.reverse.pop(op[0])

                if (op[1] == LOAD or op[1] == STORE) and S[op[0]] == cycle - 1:
                    # print("-------second-------")
                    for successor in self.reverse[op[0]]:
                        # print("-----successor-----")
                        # print(successor)
                        # print(self.dependency[successor])
                        s_opcode = self.IR[successor - 1].ir[OP]
                        if s_opcode == STORE and op[0] in self.dependency[successor] \
                                and len(self.dependency[successor]) == 1 and not self.is_serial[successor][op[0]]:
                            self.dependency[successor].remove(op[0])
                            self.dependency.pop(successor)
                            heapq.heappush(self.ready, (-self.priority[successor], (successor, s_opcode)))

            self.active = new_active
        return schedule, debug
