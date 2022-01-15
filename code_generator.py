from symbol_table import SymbolTable, Variable


class CodeGenerator:
    def __init__(self, commands, symbols):
        self.commands = commands
        self.symbols = symbols
        self.code = []
        self.iterators = []

    def gen_code(self):
        self.gen_code_from_commands(self.commands)
        self.code.append("HALT")

    def gen_code_from_commands(self, commands):
        for command in commands:
            if command[0] == "write":
                # print("write")
                value = command[1]
                register = 'a'
                register1 = 'b'
                if value[0] == "load":
                    if type(value[1]) == tuple:
                        if value[1][0] == "undeclared":
                            if value[1][1] in self.iterators:
                                address = self.symbols.get_address(value[1][1])
                                print("address: ", address)
                                self.gen_const(address, register1)
                                self.code.append(f"LOAD {register1}")
                            else:
                                raise Exception("Tried to write unknown variable or iterator")
                        elif value[1][0] == "array":
                            if type(value[1][2]) != tuple:
                                self.load_array_address_at(value[1][1], value[1][2], register, register1)
                                self.code.append(f"SWAP {register}")
                                self.code.append(f"LOAD {register}")
                            else:
                                if value[1][2][1][0] == "undeclared":
                                    if value[1][2][1][1] in self.iterators:
                                        self.load_array_address_at(value[1][1], value[1][2], 'd', register1)
                                        self.code.append(f"SWAP d")
                                        address = self.symbols.get_address(value[1][1])
                                        self.gen_const(address, register1)

                                        self.code.append(f"SWAP d")
                                        self.code.append(f"LOAD a")
                                        
                                        self.code.append(f"ADD {register1}")

                                        self.code.append(f"LOAD {register}")
                                    else:
                                        raise Exception("Tried to write unknown variable or iterator")
                                else:
                                    self.load_array_address_at(value[1][1], value[1][2], register, register1)
                                    self.code.append(f"SWAP {register}")
                                    # self.code.append(f"PUT")
                                    self.code.append(f"LOAD {register}")
                    else:
                        if self.symbols[value[1]].initialized:
                            self.load_variable_address(value[1], register)
                            self.code.append(f"LOAD {register}")
                        else:
                            raise Exception(f"Use of uninitialized variable {value[1]}")

                elif value[0] == "const":
                    address = self.symbols.get_const(value[1])
                    if address is None:
                        address = self.symbols.add_const(value[1])
                        self.gen_const(address, register1)
                        self.gen_const(value[1], register)
                        self.code.append(f"SWAP {register1}")
                        self.code.append(f"STORE {register}")
                        self.code.append(f"SWAP {register1}")
                    else:
                        self.gen_const(address, register)
                        self.code.append(f"LOAD {register}")
                self.code.append(f"PUT")

            elif command[0] == "read":

                target = command[1]
                register = 'a'
                register1 = 'b'

                if type(target) == tuple:
                    if target[0] == "undeclared":
                        if target[1] in self.symbols.iterators:
                            raise Exception(f"Reading to iterator {target[1]}")
                        else:
                            raise Exception(f"Reading to undeclared variable {target[1]}")
                    elif target[0] == "array":
                        if type(target[2]) == int:
                            self.load_array_address_at(target[1], target[2], register1, 'c')
                        else:
                            self.load_array_address_at(target[1], target[2], register1, 'c')
                else:
                    self.load_variable_address(target, register1)
                    self.symbols[target].initialized = True

                # self.code.append(f"SWAP {register}")
                self.code.append(f"GET")
                self.code.append(f"SWAP {register}")
                self.code.append(f"STORE {register1}")
                self.code.append(f"SWAP {register}")


            elif command[0] == "assign":

                target = command[1]
                expression = command[2]
                target_reg = 'a'
                second_reg = 'b'
                third_reg = 'c'
                print(expression)
                self.calculate_expression(expression)
                # self.code.append(f"PUT")
                self.code.append(f"SWAP h")

                if type(target) == tuple:
                    if target[0] == "undeclared":
                        if target[1] in self.symbols.iterators:
                            raise Exception(f"Assigning to iterator {target[1]}")
                        else:
                            raise Exception(f"Assigning to undeclared variable {target[1]}")
                    elif target[0] == "array":
                        if type(target[2]) == int:
                            self.load_array_address_at(target[1], target[2], second_reg, third_reg)
                        else:
                            if type(target[2]) != tuple:
                                self.load_array_address_at(target[1], target[2], second_reg, third_reg)
                                #TEN SWAP JEST ŹRÓŁEM PROBLEMÓW
                                # self.code.append(f"SWAP {second_reg}")
                            else:
                                if target[2][1][0] == "undeclared":
                                    if target[2][1][1] in self.iterators:
                                        self.load_array_address_at(target[1], target[2], 'd', second_reg)
                                        self.code.append(f"SWAP d")
                                        address = self.symbols.get_address(target[1])
                                        self.gen_const(address, second_reg)

                                        self.code.append(f"SWAP d")
                                        self.code.append(f"LOAD a")
                                        
                                        self.code.append(f"ADD {second_reg}")
                                        self.code.append(f"SWAP {second_reg}")
                                    else:
                                        raise Exception("Tried to write unknown variable or iterator")

                else:
                    if type(self.symbols[target]) == Variable:
                        self.load_variable_address(target, second_reg)
                        self.symbols[target].initialized = True
                    else:
                        raise Exception(f"Assigning to array {target} with no index provided")
                self.code.append(f"SWAP h")
                # self.code.append(f"PUT")

                self.code.append(f"SWAP {target_reg}")
                self.code.append(f"STORE {second_reg}")
                self.code.append(f"SWAP {target_reg}")

            elif command[0] == "if":
                condition = self.simplify_condition(command[1])
                if isinstance(condition, bool):
                    if condition:
                        self.gen_code_from_commands(command[2])
                else:
                    self.prepare_consts_before_block(command[-1])
                    condition_start = len(self.code)
                    self.check_condition(condition)
                    command_start = len(self.code)
                    self.gen_code_from_commands(command[2])
                    command_end = len(self.code)
                    for i in range(condition_start, command_start):
                        self.code[i] = self.code[i].replace('finish', str(command_end - i))

            elif command[0] == "ifelse":
                condition = self.simplify_condition(command[1])
                print(condition)
                if isinstance(condition, bool):
                    if condition:
                        self.gen_code_from_commands(command[2])
                    else:
                        self.gen_code_from_commands(command[3])
                else:
                    self.prepare_consts_before_block(command[-1])
                    condition_start = len(self.code)
                    self.check_condition(command[1])
                    if_start = len(self.code)
                    self.gen_code_from_commands(command[2])
                    self.code.append(f"JUMP finish")
                    else_start = len(self.code)
                    self.gen_code_from_commands(command[3])
                    command_end = len(self.code)
                    self.code[else_start - 1] = self.code[else_start - 1].replace('finish',
                                                                                  str(command_end - else_start + 1))
                    for i in range(condition_start, if_start):
                        self.code[i] = self.code[i].replace('finish', str(else_start - i))

            elif command[0] == "while":
                condition = self.simplify_condition(command[1])
                if isinstance(condition, bool):
                    if condition:
                        self.prepare_consts_before_block(command[-1])
                        loop_start = len(self.code)
                        self.gen_code_from_commands(command[2])
                        self.code.append(f"JUMP {loop_start - len(self.code)}")
                else:
                    self.prepare_consts_before_block(command[-1])
                    condition_start = len(self.code)
                    self.check_condition(command[1])
                    loop_start = len(self.code)
                    self.gen_code_from_commands(command[2])
                    self.code.append(f"JUMP {condition_start - len(self.code)}")
                    loop_end = len(self.code)
                    for i in range(condition_start, loop_start):
                        self.code[i] = self.code[i].replace('finish', str(loop_end - i))

            elif command[0] == "until":
                loop_start = len(self.code)
                self.gen_code_from_commands(command[2])
                condition_start = len(self.code)
                self.check_condition(command[1])
                condition_end = len(self.code)
                for i in range(condition_start, condition_end):
                    self.code[i] = self.code[i].replace('finish', str(loop_start - i))

            elif command[0] == "forup":
                if command[2][0] == command[3][0] == "const":
                    if command[2][1] > command[3][1]:
                        continue
                self.prepare_consts_before_block(command[-1])

                iterator = command[1]
                address, bound_address = self.symbols.add_iterator(iterator)
                print("iter address ", address)
                self.calculate_expression(command[3], 'e')  #do
                self.gen_const(bound_address, 'd')
                self.code.append("SWAP e")
                self.code.append("STORE d")
                self.code.append("SWAP e")

                self.calculate_expression(command[2], 'f') #od jest jednocześnie iteratorem
                self.gen_const(address, 'd')
                self.code.append("SWAP f")
                self.code.append("STORE d")
                self.code.append("SWAP f")

                self.code.append("RESET a")
                self.code.append("ADD e")
                self.code.append("SUB f")
                jpos = len(self.code)
                self.code.append("JNEG finish")
                self.code.append("JZERO finish-1")

                self.code.append("RESET a")

                self.iterators.append(iterator)
                condition_start = len(self.code)
                #JEŚLI FROM JEST WIĘKSZY lub równy TO to nie wykonuj pętli
                ls = len(self.code)
                self.code.append("JUMP loop_START")
                #obliczenia na iteratorze i sprawdzenie czy warunek jest spełniony
                self.gen_const(address, 'f')
                self.code.append("LOAD f")
                self.code.append("INC a")
                self.code.append("STORE f")
                self.code.append("SWAP f")

                self.gen_const(bound_address, 'a')
                self.code.append("LOAD a")
                self.code.append("SUB f")
                # self.code.append("INC a")

                self.code.append("JNEG 3")
                self.code.append("SWAP d")
                self.code.append("JUMP 3")
                self.code.append("SWAP d")
                ff = len(self.code)
                self.code.append("JUMP finnish")

                loop_start = len(self.code)
                self.gen_code_from_commands(command[4])
                zero_jump = len(self.code)
                self.code.append("SWAP f")
                self.code.append("JZERO 3")
                self.code.append("SWAP f")
                self.code.append("JUMP 3")
                self.code.append("SWAP f")
                finnish = len(self.code)
                self.code.append("JUMP finnish")
                self.code.append("INC f")
                self.gen_const(bound_address, 'e')
                self.code.append(f"LOAD e")
                self.code.append(f"SWAP e")
                self.code.append(f"JUMP {condition_start - len(self.code) + 1}")

                loop_end = len(self.code)

                self.code[ls] = f"JUMP {loop_start - condition_start}"
                self.code[jpos] = f"JNEG {ff - jpos}"
                self.code[jpos + 1] = f"JZERO {ff - jpos -1}"
                self.code[ff] = f"JUMP {loop_end - loop_start + 1}"
                self.code[finnish] = f"JUMP {finnish - zero_jump}"
                self.iterators.pop()
                if self.iterators:
                    address, bound_address = self.symbols.get_iterator(self.iterators[-1])
                    self.gen_const(address, 'f')
                    self.code.append(f"LOAD f")
                    self.code.append(f"SWAP f")

            elif command[0] == "fordown":
                if command[2][0] == command[3][0] == "const":
                    if command[2][1] < command[3][1]:
                        continue
                
                self.prepare_consts_before_block(command[-1])

                iterator = command[1]
                address, bound_address = self.symbols.add_iterator(iterator)
                print("iter address ", address)

                self.calculate_expression(command[3], 'e')  #do
                self.gen_const(bound_address, 'd')
                self.code.append("SWAP e")
                self.code.append("STORE d")
                # self.code.append("PUT")
                self.code.append("SWAP e")

                self.calculate_expression(command[2], 'f') #od jest jednocześnie iteratorem
                self.gen_const(address, 'd')
                self.code.append("SWAP f")
                self.code.append("STORE d")
                self.code.append("PUT")
                self.code.append("SWAP f")

                self.code.append("RESET a")
                self.code.append("ADD e")
                self.code.append("SUB f")

                jpos = len(self.code)
                self.code.append("JPOS finish")
                self.code.append("JZERO finish-1")

                self.code.append("RESET a")

                self.iterators.append(iterator)
                condition_start = len(self.code)
                #JEŚLI FROM JEST MNIEJSZY lub równy TO to nie wykonuj pętli
                ls = len(self.code)
                self.code.append("JUMP loop_START")
                #obliczenia na iteratorze i sprawdzenie czy warunek jest spełniony
                self.gen_const(address, 'f')
                self.code.append("LOAD f")
                self.code.append("DEC a")
                self.code.append("STORE f")
                self.code.append("SWAP f")

                self.gen_const(bound_address, 'a')
                self.code.append("LOAD a")
                self.code.append("SUB f")

                self.code.append("DEC a")

                self.code.append("JPOS 3")
                self.code.append("SWAP d")
                self.code.append("JUMP 3")
                self.code.append("SWAP d")
                ff = len(self.code)
                self.code.append("JUMP finnish")

                loop_start = len(self.code)
                self.gen_code_from_commands(command[4])
                zero_jump = len(self.code)
                self.code.append("SWAP f")
                self.code.append("JZERO 3")
                self.code.append("SWAP f")
                self.code.append("JUMP 3")
                self.code.append("SWAP f")
                finnish = len(self.code)
                self.code.append("JUMP finnish")
                self.code.append("INC f")
                self.gen_const(bound_address, 'e')
                self.code.append(f"LOAD e")
                self.code.append(f"SWAP e")
                self.code.append(f"JUMP {condition_start - len(self.code) + 1}")

                loop_end = len(self.code)

                self.code[ls] = f"JUMP {loop_start - condition_start}"
                self.code[jpos] = f"JPOS {ff - jpos}"
                self.code[jpos + 1] = f"JZERO {ff - jpos -1}"
                self.code[ff] = f"JUMP {loop_end - loop_start + 1}"
                self.code[finnish] = f"JUMP {finnish - zero_jump}"
                
                self.iterators.pop()
                if self.iterators:
                    address, bound_address = self.symbols.get_iterator(self.iterators[-1])
                    self.gen_const(address, 'f')
                    self.code.append(f"LOAD f")
                    self.code.append(f"SWAP f")

    def gen_const(self, const, reg='a'):
        self.code.append(f"RESET {reg}")
        self.code.append(f"SWAP {reg}")
        if const > 0:
            bits = bin(const)[2:]
            for bit in bits[:-1]:
                if bit == '1':
                    self.code.append(f"INC a")
                self.code.append(f"ADD a")
            if bits[-1] == '1':
                self.code.append(f"INC a")
        elif const < 0:
            const = -const
            bits = bin(const)[2:]
            for bit in bits[:-1]:
                if bit == '1':
                    self.code.append(f"INC a")
                self.code.append(f"ADD a")
            if bits[-1] == '1':
                self.code.append(f"INC a")
            self.code.append(f"RESET h")
            self.code.append(f"SWAP h")
            self.code.append(f"SUB h")
            self.code.append(f"RESET h")
            const = -const

        self.code.append(f"SWAP {reg}")


    def calculate_expression(self, expression, target_reg='a', second_reg='b', third_reg='c', fourth_reg='d', fifth_reg='e', sixth_reg='f', seventh_reg='g', eighth_reg='h'):
        if expression[0] == "const":
            self.gen_const(expression[1], target_reg)
        
        elif expression[0] == "load":
            if type(expression[1]) == tuple:
                if expression[1][0] == "undeclared":
                    if expression[1][1] in self.iterators:
                        address = self.symbols.get_address(expression[1][1])
                        print("address: ", address)
                        self.gen_const(address, second_reg)
                        self.code.append(f"LOAD {second_reg}")
                        self.code.append(f"SWAP {target_reg}")
                    else:
                        raise Exception("Tried to write unknown variable or iterator")
                elif expression[1][0] == "array":
                    self.load_array_at(expression[1][1], expression[1][2], target_reg, second_reg)
            else:
                if self.symbols[expression[1]].initialized:
                    self.load_variable(expression[1], target_reg)
                else:
                    raise Exception(f"Use of uninitialized variable {expression[1]}")

        else:
            if expression[1][0] == 'const':
                const, var = 1, 2
            elif expression[2][0] == 'const':
                const, var = 2, 1
            else:
                const = None

            if expression[0] == "add":
                if expression[1][0] == expression[2][0] == "const":
                    self.gen_const(expression[1][1] + expression[2][1], target_reg)

                elif expression[1] == expression[2]:
                    self.calculate_expression(expression[1], target_reg, second_reg)
                    self.code.append(f"SWAP {target_reg}")
                    self.code.append(f"ADD {target_reg}")
                    self.code.append(f"SWAP {target_reg}")

                elif const and expression[const][1] < 12:
                    self.calculate_expression(expression[var], target_reg, second_reg)
                    change = f"INC {target_reg}"
                    self.code += expression[const][1] * [change]

                else:
                    self.calculate_expression(expression[1], second_reg, third_reg)
                    self.code.append(f"SWAP {second_reg}")
                    self.code.append(f"SWAP {second_reg}")

                    self.calculate_expression(expression[2], target_reg, third_reg)
                    self.code.append(f"SWAP {target_reg}")

                    self.code.append(f"ADD {second_reg}")
                    self.code.append(f"SWAP {target_reg}")

            elif expression[0] == "sub":
                
                if expression[1][0] == expression[2][0] == "const":
                    val = expression[1][1] - expression[2][1]
                    if val:
                        self.gen_const(val, target_reg)
                    else:
                        self.code.append(f"RESET {target_reg}")

                elif expression[1] == expression[2]:
                    self.code.append(f"RESET {target_reg}")

                elif const and const == 1 and expression[const][1] == 0:
                    self.code.append(f"RESET {target_reg}")

                else:
                    self.calculate_expression(expression[1], second_reg, third_reg)
                    self.calculate_expression(expression[2], target_reg, third_reg)
                    self.code.append(f"SWAP {second_reg}")
                    self.code.append(f"SUB {second_reg}")
                    self.code.append(f"SWAP {target_reg}")

            elif expression[0] == "mul":
                if expression[1][0] == expression[2][0] == "const":
                    self.gen_const(expression[1][1] * expression[2][1], target_reg)
                    return

                if const:
                    val = expression[const][1]
                    if val == 0:
                        self.code.append(f"RESET {target_reg}")
                        return
                    elif val == 1:
                        self.calculate_expression(expression[var], target_reg, second_reg)
                        return
                    elif val & (val - 1) == 0:
                        self.calculate_expression(expression[var], target_reg, second_reg)
                        #target *= 2
                        self.code.append(f"SWAP {target_reg}")
                        while val > 1:
                            self.code.append(f"ADD a")
                            val /= 2
                        self.code.append(f"SWAP {target_reg}")

                        return

                if expression[1] == expression[2]:
                    self.calculate_expression(expression[1], second_reg, third_reg)
                    self.code.append(f"RESET {third_reg}")
                    self.code.append(f"SWAP {third_reg}")
                    self.code.append(f"ADD {second_reg}")
                    self.code.append(f"SWAP {third_reg}")

                else:
                    self.calculate_expression(expression[1], second_reg, fourth_reg)
                    self.calculate_expression(expression[2], third_reg, fourth_reg)

                self.code.append(f"RESET a")
                self.code.append(f"RESET {fourth_reg}")
                self.code.append(f"RESET {fifth_reg}")
                self.code.append(f"RESET {sixth_reg}")
                self.code.append(f"RESET {seventh_reg}")
                self.code.append(f"RESET {eighth_reg}")
                self.code.append(f"INC {fifth_reg}")
                self.code.append(f"DEC {sixth_reg}")
                self.code.append(f"SWAP {second_reg}")
                self.code.append(f"JZERO 32")
                self.code.append(f"SWAP {second_reg}")
                self.code.append(f"SWAP {third_reg}")
                self.code.append(f"JZERO 29")
                self.code.append(f"SWAP {third_reg}")

                self.code.append(f"RESET a")
                self.code.append(f"ADD {second_reg}")
                self.code.append(f"JPOS 5")
                self.code.append(f"RESET a")
                self.code.append(f"SUB {second_reg}")
                self.code.append(f"SWAP {second_reg}")
                self.code.append(f"INC {seventh_reg}")

                self.code.append(f"RESET a")
                self.code.append(f"ADD {third_reg}")
                self.code.append(f"JPOS 5")
                self.code.append(f"RESET a")
                self.code.append(f"SUB {third_reg}")
                self.code.append(f"SWAP {third_reg}")
                self.code.append(f"DEC {seventh_reg}")

                self.code.append(f"RESET a")
                self.code.append(f"SWAP {third_reg}")
                self.code.append(f"JZERO 22")
                self.code.append(f"SWAP {third_reg}")
                self.code.append(f"RESET {eighth_reg}")
                self.code.append(f"SWAP {eighth_reg}")
                self.code.append(f"ADD {third_reg}")
                self.code.append(f"SHIFT {sixth_reg}")
                self.code.append(f"SHIFT {fifth_reg}")
                self.code.append(f"SUB {third_reg}")
                self.code.append(f"JNEG 3")
                self.code.append(f"SWAP {eighth_reg}")
                self.code.append(f"JUMP 5")
                self.code.append(f"SWAP {eighth_reg}")
                self.code.append(f"SWAP {fourth_reg}")
                self.code.append(f"ADD {second_reg}")
                self.code.append(f"SWAP {fourth_reg}")
                self.code.append(f"SWAP {third_reg}")
                self.code.append(f"SHIFT {sixth_reg}")
                self.code.append(f"SWAP {third_reg}")
                self.code.append(f"SWAP {second_reg}")
                self.code.append(f"SHIFT {fifth_reg}")
                self.code.append(f"SWAP {second_reg}")
                self.code.append(f"JUMP -23")
                self.code.append(f"RESET a")
                self.code.append(f"ADD {seventh_reg}")
                self.code.append(f"JZERO 4")
                self.code.append(f"RESET a")
                self.code.append(f"SUB {fourth_reg}")
                self.code.append(f"JUMP 2")
                self.code.append(f"SWAP {fourth_reg}")
                self.code.append(f"SWAP {target_reg}")
                

            elif expression[0] == "div":
                if expression[1][0] == expression[2][0] == "const":
                    if expression[2][1] > 0:
                        self.gen_const(expression[1][1] // expression[2][1], target_reg)
                    else:
                        self.code.append(f"RESET {target_reg}")
                    return

                elif expression[1] == expression[2]:
                    self.calculate_expression(expression[1], third_reg, second_reg)
                    self.code.append(f"SWAP {third_reg}")
                    self.code.append(f"JZERO 3")
                    self.code.append(f"RESET {target_reg}")
                    self.code.append(f"INC {target_reg}")
                    return

                elif const and const == 1 and expression[const][1] == 0:
                    self.code.append(f"RESET {target_reg}")
                    return

                elif const and const == 2:
                    val = expression[const][1]
                    if val == 0:
                        self.code.append(f"RESET {target_reg}")
                        return
                    elif val == 1:
                        self.calculate_expression(expression[var], target_reg, second_reg)
                        return
                    elif val & (val - 1) == 0:
                        self.calculate_expression(expression[var], target_reg, second_reg)
                        while val > 1:
                            # print(f"(dzielenie przez 2 start)")
                            self.code.append(f"RESET h")
                            self.code.append(f"DEC h")
                            self.code.append(f"SWAP {target_reg}")
                            self.code.append(f"SHIFT h")
                            self.code.append(f"SWAP {target_reg}")

                            val /= 2
                        return

                self.calculate_expression(expression[1], fourth_reg, second_reg)
                self.calculate_expression(expression[2], fifth_reg, second_reg)

                self.perform_division(target_reg, second_reg, third_reg, fourth_reg, fifth_reg)

            elif expression[0] == "mod":
                if expression[1][0] == expression[2][0] == "const":
                    # print(f"xxx {expression[1][1]} % {expression[2][1]}")
                    self.gen_const(expression[1][1] % expression[2][1], target_reg)
                    return

                elif expression[1] == expression[2]:
                    self.code.append(f"RESET {target_reg}")
                    return

                # elif const and const == 1 and expression[const][1] == 0:
                #     self.code.append(f"RESET {target_reg}")
                #     return

                # elif const and const == 2:
                #     val = expression[const][1]
                #     if val < 2:
                #         self.code.append(f"RESET {target_reg}")
                #         return
                #     elif val == 2:
                #         self.calculate_expression(expression[var], second_reg, target_reg)
                #         self.code.append(f"RESET {target_reg}")
                #         self.code.append(f"JODD {second_reg} 2")
                #         self.code.append(f"JUMP 2")
                #         self.code.append(f"INC {target_reg}")
                #         return

                self.calculate_expression(expression[1], fourth_reg, second_reg)
                self.calculate_expression(expression[2], fifth_reg, second_reg)

                self.code.append(f"RESET {second_reg}")
                self.code.append(f"RESET {third_reg}")

                self.code.append(f"SWAP {fourth_reg}")
                self.code.append(f"JZERO 3")
                self.code.append(f"SWAP {fourth_reg}")
                self.code.append(f"SWAP {fifth_reg}")
                self.code.append(f"JZERO 84")
                self.code.append(f"SWAP {fifth_reg}")

                self.code.append(f"RESET a")
                self.code.append(f"ADD {fourth_reg}")
                self.code.append(f"ADD {fifth_reg}")
                self.code.append(f"JZERO -5")

                self.code.append(f"RESET a")
                self.code.append(f"ADD {fourth_reg}")
                self.code.append(f"JPOS 12")
                self.code.append(f"RESET a")
                self.code.append(f"SUB {fourth_reg}")
                self.code.append(f"SWAP {fourth_reg}")

                self.code.append(f"RESET a")
                self.code.append(f"ADD {fifth_reg}")
                self.code.append(f"JPOS 12")
                self.code.append(f"RESET a")
                self.code.append(f"INC {second_reg}")
                self.code.append(f"SUB {fifth_reg}")
                self.code.append(f"SWAP {fifth_reg}")
                self.code.append(f"JUMP 9")

                self.code.append(f"RESET a")
                self.code.append(f"ADD {fifth_reg}")
                self.code.append(f"JPOS 6")
                self.code.append(f"RESET a")
                self.code.append(f"INC {second_reg}")
                self.code.append(f"SUB {fifth_reg}")
                self.code.append(f"SWAP {fifth_reg}")
                self.code.append(f"JUMP 60")

                self.code.append(f"RESET a")
                self.code.append(f"ADD {fourth_reg}")
                self.code.append(f"RESET {seventh_reg}")
                self.code.append(f"DEC {third_reg}")
                self.code.append(f"JZERO 4")
                self.code.append(f"SHIFT {third_reg}")
                self.code.append(f"INC {seventh_reg}")
                self.code.append(f"JUMP -3")
                self.code.append(f"INC {third_reg}")
                self.code.append(f"SWAP {seventh_reg}")
                self.code.append(f"JNEG 40")
                self.code.append(f"SWAP {seventh_reg}")

                self.code.append(f"RESET a")
                self.code.append(f"ADD {fourth_reg}")
                self.code.append(f"SWAP {sixth_reg}")

                self.code.append(f"RESET a")
                self.code.append(f"ADD {seventh_reg}")
                self.code.append(f"JZERO 9")
                self.code.append(f"SWAP {eighth_reg}")
                self.code.append(f"RESET a")
                self.code.append(f"SWAP {sixth_reg}")
                self.code.append(f"DEC {sixth_reg}")
                self.code.append(f"SHIFT {sixth_reg}")
                self.code.append(f"SWAP {sixth_reg}")
                self.code.append(f"ADD {eighth_reg}")
                self.code.append(f"JUMP -8")

                self.code.append(f"RESET a")
                self.code.append(f"INC a")
                self.code.append(f"SWAP {third_reg}")
                self.code.append(f"SHIFT {third_reg}")
                self.code.append(f"SWAP {third_reg}")

                self.code.append(f"RESET a")
                self.code.append(f"ADD {sixth_reg}")
                self.code.append(f"RESET {eighth_reg}")
                self.code.append(f"DEC {eighth_reg}")
                self.code.append(f"SHIFT {eighth_reg}")
                self.code.append(f"INC {eighth_reg}")
                self.code.append(f"INC {eighth_reg}")
                self.code.append(f"SHIFT {eighth_reg}")
                self.code.append(f"SUB {sixth_reg}")
                self.code.append(f"JZERO 2")
                self.code.append(f"INC {third_reg}")

                self.code.append(f"RESET a")
                self.code.append(f"ADD {third_reg}")
                self.code.append(f"SUB {fifth_reg}")
                self.code.append(f"JNEG 3")
                self.code.append(f"SWAP {third_reg}")
                self.code.append(f"RESET a")

                self.code.append(f"DEC {seventh_reg}")
                self.code.append(f"JUMP -40")
                self.code.append(f"SWAP {third_reg}")
                self.code.append(f"SWAP {second_reg}")
                self.code.append(f"JZERO 4")
                self.code.append(f"DEC a")
                self.code.append(f"SUB {second_reg}")
                self.code.append(f"SWAP {second_reg}")
                self.code.append(f"SWAP {second_reg}")
                self.code.append(f"JUMP 61")
                self.code.append(f"JUMP -1")

                self.code.append(f"RESET a")
                self.code.append(f"ADD {fourth_reg}")
                self.code.append(f"RESET {seventh_reg}")
                self.code.append(f"DEC {third_reg}")
                self.code.append(f"JZERO 4")
                self.code.append(f"SHIFT {third_reg}")
                self.code.append(f"INC {seventh_reg}")
                self.code.append(f"JUMP -3")
                self.code.append(f"INC {third_reg}")
                self.code.append(f"SWAP {seventh_reg}")
                self.code.append(f"JNEG 40")
                self.code.append(f"SWAP {seventh_reg}")

                self.code.append(f"RESET a")
                self.code.append(f"ADD {fourth_reg}")
                self.code.append(f"SWAP {sixth_reg}")

                self.code.append(f"RESET a")
                self.code.append(f"ADD {seventh_reg}")
                self.code.append(f"JZERO 9")
                self.code.append(f"SWAP {eighth_reg}")
                self.code.append(f"RESET a")
                self.code.append(f"SWAP {sixth_reg}")
                self.code.append(f"DEC {sixth_reg}")
                self.code.append(f"SHIFT {sixth_reg}")
                self.code.append(f"SWAP {sixth_reg}")
                self.code.append(f"ADD {eighth_reg}")
                self.code.append(f"JUMP -8")

                self.code.append(f"RESET a")
                self.code.append(f"INC a")
                self.code.append(f"SWAP {third_reg}")
                self.code.append(f"SHIFT {third_reg}")
                self.code.append(f"SWAP {third_reg}")

                self.code.append(f"RESET a")
                self.code.append(f"ADD {sixth_reg}")
                self.code.append(f"RESET {eighth_reg}")
                self.code.append(f"DEC {eighth_reg}")
                self.code.append(f"SHIFT {eighth_reg}")
                self.code.append(f"INC {eighth_reg}")
                self.code.append(f"INC {eighth_reg}")
                self.code.append(f"SHIFT {eighth_reg}")
                self.code.append(f"SUB {sixth_reg}")
                self.code.append(f"JZERO 2")
                self.code.append(f"INC {third_reg}")

                self.code.append(f"RESET a")
                self.code.append(f"ADD {third_reg}")
                self.code.append(f"SUB {fifth_reg}")
                self.code.append(f"JNEG 3")
                self.code.append(f"SWAP {third_reg}")
                self.code.append(f"RESET a")

                self.code.append(f"DEC {seventh_reg}")
                self.code.append(f"JUMP -40")
                self.code.append(f"RESET a")
                self.code.append(f"SUB {third_reg}")
                self.code.append(f"ADD {fifth_reg}")
                self.code.append(f"SWAP {second_reg}")
                self.code.append(f"JZERO 4")
                self.code.append(f"DEC a")
                self.code.append(f"SUB {second_reg}")
                self.code.append(f"SWAP {second_reg}")
                self.code.append(f"SWAP {second_reg}")
                self.code.append(f"SWAP {target_reg}")


    def perform_division(self, target_reg='a', second_reg='b', third_reg='c', fourth_reg='d', fifth_reg='e', sixth_reg='f', seventh_reg='g', eighth_reg='h'):

        self.code.append(f"RESET {second_reg}")
        self.code.append(f"RESET {third_reg}")

        self.code.append(f"SWAP {fourth_reg}")
        self.code.append(f"JZERO 3")
        self.code.append(f"SWAP {fourth_reg}")
        self.code.append(f"SWAP {fifth_reg}")
        self.code.append(f"JZERO 76")
        self.code.append(f"SWAP {fifth_reg}")

        self.code.append(f"RESET a")
        self.code.append(f"ADD {fourth_reg}")
        self.code.append(f"JPOS 11")
        self.code.append(f"RESET a")
        self.code.append(f"SUB {fourth_reg}")
        self.code.append(f"SWAP {fourth_reg}")

        self.code.append(f"RESET a")
        self.code.append(f"ADD {fifth_reg}")
        self.code.append(f"JPOS 11")
        self.code.append(f"RESET a")
        self.code.append(f"SUB {fifth_reg}")
        self.code.append(f"SWAP {fifth_reg}")
        self.code.append(f"JUMP 8")

        self.code.append(f"RESET a")
        self.code.append(f"ADD {fifth_reg}")
        self.code.append(f"JPOS 5")
        self.code.append(f"RESET a")
        self.code.append(f"SUB {fifth_reg}")
        self.code.append(f"SWAP {fifth_reg}")
        self.code.append(f"JUMP 58")

        self.code.append(f"RESET a")
        self.code.append(f"ADD {fourth_reg}")
        self.code.append(f"RESET {seventh_reg}")
        self.code.append(f"DEC {third_reg}")
        self.code.append(f"JZERO 4")
        self.code.append(f"SHIFT {third_reg}")
        self.code.append(f"INC {seventh_reg}")
        self.code.append(f"JUMP -3")
        self.code.append(f"INC {third_reg}")
        self.code.append(f"SWAP {seventh_reg}")
        self.code.append(f"JNEG 44")
        self.code.append(f"SWAP {seventh_reg}")

        self.code.append(f"RESET a")
        self.code.append(f"ADD {fourth_reg}")
        self.code.append(f"SWAP {sixth_reg}")

        self.code.append(f"RESET a")
        self.code.append(f"ADD {seventh_reg}")
        self.code.append(f"JZERO 9")
        self.code.append(f"SWAP {eighth_reg}")
        self.code.append(f"RESET a")
        self.code.append(f"SWAP {sixth_reg}")
        self.code.append(f"DEC {sixth_reg}")
        self.code.append(f"SHIFT {sixth_reg}")
        self.code.append(f"SWAP {sixth_reg}")
        self.code.append(f"ADD {eighth_reg}")
        self.code.append(f"JUMP -8")

        self.code.append(f"RESET a")
        self.code.append(f"INC a")
        self.code.append(f"SWAP {second_reg}")
        self.code.append(f"SHIFT {second_reg}")
        self.code.append(f"SWAP {second_reg}")
        self.code.append(f"SWAP {third_reg}")
        self.code.append(f"SHIFT {third_reg}")
        self.code.append(f"SWAP {third_reg}")

        self.code.append(f"RESET a")
        self.code.append(f"ADD {sixth_reg}")
        self.code.append(f"RESET {eighth_reg}")
        self.code.append(f"DEC {eighth_reg}")
        self.code.append(f"SHIFT {eighth_reg}")
        self.code.append(f"INC {eighth_reg}")
        self.code.append(f"INC {eighth_reg}")
        self.code.append(f"SHIFT {eighth_reg}")
        self.code.append(f"SUB {sixth_reg}")
        self.code.append(f"JZERO 2")
        self.code.append(f"INC {third_reg}")

        self.code.append(f"RESET a")
        self.code.append(f"ADD {third_reg}")
        self.code.append(f"SUB {fifth_reg}")
        self.code.append(f"JNEG 3")
        self.code.append(f"INC {second_reg}")
        self.code.append(f"SWAP {third_reg}")
        self.code.append(f"RESET a")

        self.code.append(f"DEC {seventh_reg}")
        self.code.append(f"JUMP -44")
        self.code.append(f"SWAP {second_reg}")
        self.code.append(f"JUMP 57")

        self.code.append(f"RESET a")
        self.code.append(f"ADD {fourth_reg}")
        self.code.append(f"RESET {seventh_reg}")
        self.code.append(f"DEC {third_reg}")
        self.code.append(f"JZERO 4")
        self.code.append(f"SHIFT {third_reg}")
        self.code.append(f"INC {seventh_reg}")
        self.code.append(f"JUMP -3")
        self.code.append(f"INC {third_reg}")
        self.code.append(f"SWAP {seventh_reg}")
        self.code.append(f"JNEG 44")
        self.code.append(f"SWAP {seventh_reg}")

        self.code.append(f"RESET a")
        self.code.append(f"ADD {fourth_reg}")
        self.code.append(f"SWAP {sixth_reg}")

        self.code.append(f"RESET a")
        self.code.append(f"ADD {seventh_reg}")
        self.code.append(f"JZERO 9")
        self.code.append(f"SWAP {eighth_reg}")
        self.code.append(f"RESET a")
        self.code.append(f"SWAP {sixth_reg}")
        self.code.append(f"DEC {sixth_reg}")
        self.code.append(f"SHIFT {sixth_reg}")
        self.code.append(f"SWAP {sixth_reg}")
        self.code.append(f"ADD {eighth_reg}")
        self.code.append(f"JUMP -8")

        self.code.append(f"RESET a")
        self.code.append(f"INC a")
        self.code.append(f"SWAP {second_reg}")
        self.code.append(f"SHIFT {second_reg}")
        self.code.append(f"SWAP {second_reg}")
        self.code.append(f"SWAP {third_reg}")
        self.code.append(f"SHIFT {third_reg}")
        self.code.append(f"SWAP {third_reg}")

        self.code.append(f"RESET a")
        self.code.append(f"ADD {sixth_reg}")
        self.code.append(f"RESET {eighth_reg}")
        self.code.append(f"DEC {eighth_reg}")
        self.code.append(f"SHIFT {eighth_reg}")
        self.code.append(f"INC {eighth_reg}")
        self.code.append(f"INC {eighth_reg}")
        self.code.append(f"SHIFT {eighth_reg}")
        self.code.append(f"SUB {sixth_reg}")
        self.code.append(f"JZERO 2")
        self.code.append(f"INC {third_reg}")

        self.code.append(f"RESET a")
        self.code.append(f"ADD {third_reg}")
        self.code.append(f"SUB {fifth_reg}")
        self.code.append(f"JNEG 3")
        self.code.append(f"INC {second_reg}")
        self.code.append(f"SWAP {third_reg}")
        self.code.append(f"RESET a")

        self.code.append(f"DEC {seventh_reg}")
        self.code.append(f"JUMP -44")
        self.code.append(f"RESET a")
        self.code.append(f"SUB {second_reg}")

        self.code.append(f"SWAP {target_reg}")

    def simplify_condition(self, condition):
        print(condition)
        if condition[1][0] == "const" and condition[2][0] == "const":
            if condition[0] == "le":
                return condition[1][1] <= condition[2][1]
            elif condition[0] == "ge":
                return condition[1][1] >= condition[2][1]
            elif condition[0] == "lt":
                return condition[1][1] < condition[2][1]
            elif condition[0] == "gt":
                return condition[1][1] > condition[2][1]
            elif condition[0] == "eq":
                return condition[1][1] == condition[2][1]
            elif condition[0] == "ne":
                return condition[1][1] != condition[2][1]

        elif condition[1] == condition[2]:
            if condition[0] in ["ge", "le", "eq"]:
                return True
            else:
                return False
        else:
            return condition

    def check_condition(self, condition, first_reg='a', second_reg='b', third_reg='c'):
        print(condition[0])
        self.calculate_expression(condition[1], third_reg, second_reg)
        self.calculate_expression(condition[2], second_reg, first_reg)

        if condition[0] == "le":
            self.code.append(f"SWAP {second_reg}")
            self.code.append(f"SUB {third_reg}")
            self.code.append(f"JNEG finish")

        elif condition[0] == "ge":
            self.code.append(f"SWAP {second_reg}")
            self.code.append(f"SUB {third_reg}")
            self.code.append(f"JPOS finish")

        elif condition[0] == "lt":
            self.code.append(f"SWAP {third_reg}")
            self.code.append(f"SUB {second_reg}")
            self.code.append(f"JZERO finish")
            self.code.append(f"JPOS finish")

        elif condition[0] == "gt":
            self.code.append(f"SWAP {third_reg}")
            self.code.append(f"SUB {second_reg}")
            self.code.append(f"JZERO finish")
            self.code.append(f"JNEG finish")

        elif condition[0] == "eq":
            self.code.append(f"SWAP {third_reg}")
            self.code.append(f"SUB {second_reg}")
            self.code.append(f"JZERO 2")
            self.code.append(f"JUMP finish")
            # self.code.append(f"SUB {second_reg} {third_reg}")
            # self.code.append(f"JZERO {second_reg} 2")
            # self.code.append(f"JUMP finish")
            # JUMP HERE IS A != B
        elif condition[0] == "ne":
            self.code.append(f"SWAP {third_reg}")
            self.code.append(f"SUB {second_reg}")
            self.code.append(f"JZERO finish")

    def load_array_at(self, array, index, reg1, reg2):
        self.load_array_address_at(array, index, reg1, reg2)
        self.code.append(f"LOAD {reg1}")
        self.code.append(f"SWAP {reg1}")

    def load_array_address_at(self, array, index, reg1, reg2):
        # print(array, index, reg1, reg2)
        if type(index) == int:
            address = self.symbols.get_address((array, index))
            self.gen_const(address, reg1)

        elif type(index) == tuple:
            if type(index[1]) == tuple:
                if index[1][0] == "undeclared":
                    address = self.symbols.get_address(index[1][1])
                    self.gen_const(address, reg2)
                    self.code.append(f"SWAP {reg2}")
                    return
                else:
                    self.load_variable(index[1][1], reg2, declared=False)
            else:
                if not self.symbols[index[1]].initialized:
                    raise Exception(f"Trying to use {array}({index[1]}) where variable {index[1]} is uninitialized")
                self.load_variable(index[1], reg2)
                
                var = self.symbols.get_variable(array)
                self.gen_const(var.memory_offset - var.first_index, reg1)
                # print(var.memory_offset - var.first_index)

                self.code.append(f"SWAP {reg1}")
                self.code.append(f"ADD {reg2}")
                self.code.append(f"SWAP {reg1}")
                return

            var = self.symbols.get_variable(array)
            self.gen_const(var.memory_offset - var.first_index, reg1)
            # print(var.memory_offset - var.first_index)

            self.code.append(f"SWAP {reg1}")
            self.code.append(f"ADD {reg2}")
            # self.code.append(f"PUT")
            self.code.append(f"SWAP {reg1}")

            # self.code.append(f"SWAP {reg2}")
            # self.code.append(f"ADD {reg1}")
            # # self.code.append(f"PUT")
            # self.code.append(f"SWAP {reg1}")


    def load_variable(self, name, reg, declared=True):
        # print("load_variable: ", name)

        if not declared and self.iterators and name == self.iterators[-1]:
            self.code.append(f"RESET {reg}")
            self.code.append(f"SWAP f")
            self.code.append(f"ADD {reg}")
            self.code.append(f"SWAP f")
        else:
            self.load_variable_address(name, reg, declared)
            self.code.append(f"LOAD {reg}")
            self.code.append(f"SWAP {reg}")

    def load_variable_address(self, name, reg, declared=True):
        if declared or name in self.iterators:
            address = self.symbols.get_address(name)
            # print("address: ", address)
            self.gen_const(address, reg)
            if self.iterators and name == self.iterators[-1]:
                self.code.append(f"STORE {reg}")
        else:
            raise Exception(f"Undeclared variable {name}")

    def prepare_consts_before_block(self, consts, reg1='a', reg2='b', reg3='c'):
        for c in consts:
            address = self.symbols.get_const(c)
            if address is None:
                address = self.symbols.add_const(c)
                print(c, address)
                self.gen_const(address, reg3)
                self.gen_const(c, reg2)
                self.code.append(f"SWAP {reg2}")
                self.code.append(f"STORE {reg3}")