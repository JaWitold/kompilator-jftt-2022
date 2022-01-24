from memory import Variable

def check_static_condition(condition):
  if condition[1][0] == "const" and condition[2][0] == "const":
    if condition[0] == "leq":
      return condition[1][1] <= condition[2][1]
    elif condition[0] == "geq":
      return condition[1][1] >= condition[2][1]
    elif condition[0] == "le":
      return condition[1][1] < condition[2][1]
    elif condition[0] == "ge":
      return condition[1][1] > condition[2][1]
    elif condition[0] == "eq":
      return condition[1][1] == condition[2][1]
    elif condition[0] == "neq":
      return condition[1][1] != condition[2][1]
  elif condition[1] == condition[2]:
    if condition[0] in ["geq", "leq", "eq"]:
      return True
    else:
      return False
  else:
    return condition

class Compiler:
  def __init__(self, commands, memory):
    self.commands = commands
    self.memory = memory
    self.assembly = []
    self.iterators = []

  def compile(self):
    self.generate_assembly(self.commands)
    self.assembly.append("HALT")
    return self.assembly

  def generate_assembly(self, commands):
    for command in commands:
      if command[0] == "assign":
        target = command[1]
        expression = command[2]
        target_reg = 'a'
        second_reg = 'b'
        third_reg = 'c'
        self.calculate_expression(expression)
        self.assembly.append(f"SWAP h")
        if type(target) == tuple:
          if target[0] == "undeclared":
            if target[1] in self.memory.iterators:
              raise Exception(f"Zabroniona modyfikacja iteratora i {target[1]}")
            else:
              raise Exception(f"Niezadeklarowana zmienna {target[1]}")
          elif target[0] == "array":
            if type(target[2]) == int:
              self.load_array_address_at(target[1], target[2], second_reg, third_reg)
            else:
              if type(target[2]) != tuple:
                self.load_array_address_at(target[1], target[2], second_reg, third_reg)
              else:
                if target[2][1][0] == "undeclared":
                  if target[2][1][1] in self.iterators:
                    self.load_array_address_at(target[1], target[2], second_reg, third_reg)
                  else:
                    raise Exception(f"Niezadeklarowana zmienna lub iterator {target[2][1][1]}")
                else:
                  self.load_array_address_at(target[1], target[2], second_reg, third_reg)
        else:
          if type(self.memory[target]) == Variable:
            self.load_variable_address(target, second_reg)
            self.memory[target].initialized = True
          else:
            raise Exception(f"Niewłaściwe użycie zmiennej tablicowej {target}")
        self.assembly.append(f"SWAP h")
        self.assembly.append(f"SWAP {target_reg}")
        self.assembly.append(f"STORE {second_reg}")
        self.assembly.append(f"SWAP {target_reg}")
      elif command[0] == "if_else":
        condition = check_static_condition(command[1])
        if isinstance(condition, bool):
          if condition:
            self.generate_assembly(command[2])
          else:
            self.generate_assembly(command[3])
        else:
          self.prepare_consts(command[-1])
          condition_start = len(self.assembly)
          self.check_condition(command[1])
          if_start = len(self.assembly)
          self.generate_assembly(command[2])
          self.assembly.append(f"JUMP finish")
          else_start = len(self.assembly)
          self.generate_assembly(command[3])
          command_end = len(self.assembly)
          self.assembly[else_start - 1] = self.assembly[else_start - 1].replace('finish', str(command_end - else_start + 1))
          for i in range(condition_start, if_start):
            self.assembly[i] = self.assembly[i].replace('finish', str(else_start - i))
          self.remove_prepared_consts(command[-1])
      elif command[0] == "if":
        condition = check_static_condition(command[1])
        if isinstance(condition, bool):
          if condition:
            self.generate_assembly(command[2])
        else:
          self.prepare_consts(command[-1])
          condition_start = len(self.assembly)
          self.check_condition(condition)
          command_start = len(self.assembly)
          self.generate_assembly(command[2])
          command_end = len(self.assembly)
          for i in range(condition_start, command_start):
            self.assembly[i] = self.assembly[i].replace('finish', str(command_end - i))
          self.remove_prepared_consts(command[-1])
      elif command[0] == "while":
        condition = check_static_condition(command[1])
        if isinstance(condition, bool):
          if condition:
            self.prepare_consts(command[-1])
            loop_start = len(self.assembly)
            self.generate_assembly(command[2])
            self.assembly.append(f"JUMP {loop_start - len(self.assembly)}")
            self.remove_prepared_consts(command[-1])
        else:
          self.prepare_consts(command[-1])
          condition_start = len(self.assembly)
          self.check_condition(command[1])
          loop_start = len(self.assembly)
          self.generate_assembly(command[2])
          self.assembly.append(f"JUMP {condition_start - len(self.assembly)}")
          loop_end = len(self.assembly)
          for i in range(condition_start, loop_start):
            self.assembly[i] = self.assembly[i].replace('finish', str(loop_end - i))
          self.remove_prepared_consts(command[-1])
      elif command[0] == "repeat":
        loop_start = len(self.assembly)
        self.generate_assembly(command[2])
        condition_start = len(self.assembly)
        self.check_condition(command[1])
        condition_end = len(self.assembly)
        for i in range(condition_start, condition_end):
          self.assembly[i] = self.assembly[i].replace('finish', str(loop_start - i))
      elif command[0] == "for_to":
        if command[2][0] == command[3][0] == "const":
          if command[2][1] > command[3][1]:
            continue
        self.prepare_consts(command[-1])
        iterator = command[1]
        address, bound_address = self.memory.set_iterator(iterator)
        self.calculate_expression(command[3], 'e')
        self.prepare_const(bound_address, 'd')
        self.assembly.append("SWAP e")
        self.assembly.append("STORE d")
        self.assembly.append("SWAP e")
        self.calculate_expression(command[2], 'f')
        self.prepare_const(address, 'd')
        self.assembly.append("SWAP f")
        self.assembly.append("STORE d")
        self.assembly.append("SWAP f")
        self.assembly.append("RESET a")
        self.assembly.append("ADD e")
        self.assembly.append("SUB f")
        jpos = len(self.assembly)
        self.assembly.append("JNEG finish")
        self.assembly.append("RESET a")
        self.iterators.append(iterator)
        condition_start = len(self.assembly)
        ls = len(self.assembly)
        self.assembly.append("JUMP loop_START")
        self.prepare_const(address, 'f')
        self.assembly.append("LOAD f")
        self.assembly.append("INC a")
        self.assembly.append("STORE f")
        self.assembly.append("SWAP f")
        self.prepare_const(bound_address, 'a')
        self.assembly.append("LOAD a")
        self.assembly.append("SUB f")
        self.assembly.append("JNEG 3")
        self.assembly.append("SWAP d")
        self.assembly.append("JUMP 3")
        self.assembly.append("SWAP d")
        ff = len(self.assembly)
        self.assembly.append("JUMP finish")
        loop_start = len(self.assembly)
        self.generate_assembly(command[4])
        zero_jump = len(self.assembly)
        self.assembly.append("SWAP f")
        self.assembly.append("JZERO 3")
        self.assembly.append("SWAP f")
        self.assembly.append("JUMP 3")
        self.assembly.append("SWAP f")
        finish = len(self.assembly)
        self.assembly.append("JUMP finish")
        self.assembly.append("INC f")
        self.prepare_const(bound_address, 'e')
        self.assembly.append(f"LOAD e")
        self.assembly.append(f"SWAP e")
        self.assembly.append(f"JUMP {condition_start - len(self.assembly) + 1}")
        loop_end = len(self.assembly)
        self.assembly[ls] = f"JUMP {loop_start - condition_start}"
        self.assembly[jpos] = f"JNEG {ff - jpos}"
        self.assembly[ff] = f"JUMP {loop_end - loop_start + 1}"
        self.assembly[finish] = f"JUMP {finish - zero_jump}"
        self.iterators.pop()
        self.memory.memory_offset -= 2
        if self.iterators:
          address, bound_address = self.memory.get_iterator(self.iterators[-1])
          self.prepare_const(address, 'f')
          self.assembly.append(f"LOAD f")
          self.assembly.append(f"SWAP f")
        self.remove_prepared_consts(command[-1])

      elif command[0] == "for_down_to":
        if command[2][0] == command[3][0] == "const":
          if command[2][1] < command[3][1]:
            continue
        self.prepare_consts(command[-1])
        iterator = command[1]
        address, bound_address = self.memory.set_iterator(iterator)
        self.calculate_expression(command[3], 'e')
        self.prepare_const(bound_address, 'd')
        self.assembly.append("SWAP e")
        self.assembly.append("STORE d")
        self.assembly.append("SWAP e")
        self.calculate_expression(command[2], 'f')
        self.prepare_const(address, 'd')
        self.assembly.append("SWAP f")
        self.assembly.append("STORE d")
        self.assembly.append("SWAP f")
        self.assembly.append("RESET a")
        self.assembly.append("ADD e")
        self.assembly.append("SUB f")
        jpos = len(self.assembly)
        self.assembly.append("JPOS finish")
        self.assembly.append("RESET a")
        self.iterators.append(iterator)
        condition_start = len(self.assembly)
        ls = len(self.assembly)
        self.assembly.append("JUMP loop_START")
        self.prepare_const(address, 'f')
        self.assembly.append("LOAD f")
        self.assembly.append("DEC a")
        self.assembly.append("STORE f")
        self.assembly.append("SWAP f")
        self.prepare_const(bound_address, 'a')
        self.assembly.append("LOAD a")
        self.assembly.append("SUB f")
        self.assembly.append("JPOS 3")
        self.assembly.append("SWAP d")
        self.assembly.append("JUMP 3")
        self.assembly.append("SWAP d")
        ff = len(self.assembly)
        self.assembly.append("JUMP finish")
        loop_start = len(self.assembly)
        self.generate_assembly(command[4])
        zero_jump = len(self.assembly)
        self.assembly.append("SWAP f")
        self.assembly.append("JZERO 3")
        self.assembly.append("SWAP f")
        self.assembly.append("JUMP 3")
        self.assembly.append("SWAP f")
        finish = len(self.assembly)
        self.assembly.append("JUMP finish")
        self.assembly.append("INC f")
        self.prepare_const(bound_address, 'e')
        self.assembly.append(f"LOAD e")
        self.assembly.append(f"SWAP e")
        self.assembly.append(f"JUMP {condition_start - len(self.assembly) + 1}")
        loop_end = len(self.assembly)
        self.assembly[ls] = f"JUMP {loop_start - condition_start}"
        self.assembly[jpos] = f"JPOS {ff - jpos}"
        self.assembly[ff] = f"JUMP {loop_end - loop_start + 1}"
        self.assembly[finish] = f"JUMP {finish - zero_jump}"
        self.iterators.pop()
        self.memory.memory_offset -= 2
        if self.iterators:
          address, bound_address = self.memory.get_iterator(self.iterators[-1])
          self.prepare_const(address, 'f')
          self.assembly.append(f"LOAD f")
          self.assembly.append(f"SWAP f")
        self.remove_prepared_consts(command[-1])
      elif command[0] == "read":
        target = command[1]
        target_reg = 'a'
        second_reg = 'b'
        third_reg = 'c'
        if type(target) == tuple:
          if target[0] == "undeclared":
            if target[1] in self.memory.iterators:
              raise Exception(f"Zabroniona modyfikacja iteratora {target[1]}")
            else:
              raise Exception(f"Niezadeklarowana zmienna {target[1]}")
          elif target[0] == "array":
            if type(target[2]) == int:
              self.load_array_address_at(target[1], target[2], second_reg, third_reg)
            else:
              self.load_array_address_at(target[1], target[2], second_reg, third_reg)
        else:
          self.load_variable_address(target, second_reg)
          self.memory[target].initialized = True
        self.assembly.append(f"GET")
        self.assembly.append(f"SWAP {target_reg}")
        self.assembly.append(f"STORE {second_reg}")
        self.assembly.append(f"SWAP {target_reg}")
      elif command[0] == "write":
        value = command[1]
        target_reg = 'a'
        second_reg = 'b'
        third_reg = 'c'
        if value[0] == "load":
          if type(value[1]) == tuple:
            if value[1][0] == "undeclared":
              if value[1][1] in self.iterators:
                address = self.memory.get_address(value[1][1])
                self.prepare_const(address, second_reg)
                self.assembly.append(f"LOAD {second_reg}")
              else:
                raise Exception(f"Niezadeklarowana zmienna lub iterator {value[1][1]}")
            elif value[1][0] == "array":
              if type(value[1][2]) != tuple:
                self.load_array_address_at(value[1][1], value[1][2], target_reg, second_reg)
                self.assembly.append(f"SWAP {target_reg}")
                self.assembly.append(f"LOAD {target_reg}")
              else:
                if value[1][2][1][0] == "undeclared":
                  if value[1][2][1][1] in self.iterators:
                    self.load_array_address_at(value[1][1], value[1][2], third_reg, second_reg)
                    self.assembly.append(f"SWAP {target_reg}")
                    self.assembly.append(f"LOAD {third_reg}")
                  else:
                    raise Exception(f"Niezadeklarowana zmienna lub iterator {value[1][2][1][1]}")
                else:
                  self.load_array_address_at(value[1][1], value[1][2], target_reg, second_reg)
                  self.assembly.append(f"SWAP {target_reg}")
                  self.assembly.append(f"LOAD {target_reg}")
          else:
            if self.memory[value[1]].initialized:
              self.load_variable_address(value[1], target_reg)
              self.assembly.append(f"LOAD {target_reg}")
            else:
              raise Exception(f"Użycie niezainicjalizowanej zmiennej {value[1]}")
        elif value[0] == "const":
          address = self.memory.get_const(value[1])
          if address is None:
            self.prepare_const(value[1], second_reg)
            self.assembly.append(f"SWAP {second_reg}")
          else:
            self.prepare_const(address, target_reg)
            self.assembly.append(f"LOAD {target_reg}")
        self.assembly.append(f"PUT")

  def calculate_expression(self, expression, target_reg='a', second_reg='b', third_reg='c', fourth_reg='d', fifth_reg='e', sixth_reg='f', seventh_reg='g', eighth_reg='h'):
    if expression[0] == "const":
      self.prepare_const(expression[1], target_reg)
    elif expression[0] == "load":
      if type(expression[1]) == tuple:
        if expression[1][0] == "undeclared":
          if expression[1][1] in self.iterators:
            address = self.memory.get_address(expression[1][1])
            self.prepare_const(address, second_reg)
            self.assembly.append(f"LOAD {second_reg}")
            self.assembly.append(f"SWAP {target_reg}")
          else:
            raise Exception(f"Niezadeklarowana zmienna lub iterator {expression[1][1]}")
        elif expression[1][0] == "array":
          if type(expression[1][2]) != tuple:
            self.load_array_at(expression[1][1], expression[1][2], target_reg, second_reg)
          else:
            if expression[1][2][1][0] == "undeclared":
              if expression[1][2][1][1] in self.iterators:
                self.load_array_at(expression[1][1], expression[1][2], target_reg, second_reg)
              else:
                raise Exception(f"Niezainicjalizowany iterator {expression[1][2][1][0]}")
            else:
              self.load_array_at(expression[1][1], expression[1][2], target_reg, second_reg)
      else:
        if self.memory[expression[1]].initialized:
          self.load_variable(expression[1], target_reg)
        else:
          raise Exception(f"Niezainicjalizowana zmienna {expression[1]}")

    else:
      if expression[1][0] == 'const':
        const, variable = 1, 2
      elif expression[2][0] == 'const':
        const, variable = 2, 1
      else:
        const = None
      if expression[0] == "plus":
        if expression[1][0] == expression[2][0] == "const":
          self.prepare_const(expression[1][1] + expression[2][1], target_reg)
        elif expression[1] == expression[2]:
          self.calculate_expression(expression[1], target_reg, second_reg)
          self.assembly.append(f"SWAP {target_reg}")
          self.assembly.append(f"ADD {target_reg}")
          self.assembly.append(f"SWAP {target_reg}")
        elif const and expression[const][1] < 10:
          self.calculate_expression(expression[variable], target_reg, second_reg)
          change = f"INC {target_reg}"
          self.assembly += expression[const][1] * [change]
        else:
          self.calculate_expression(expression[1], second_reg, third_reg)
          self.assembly.append(f"SWAP {second_reg}")
          self.assembly.append(f"SWAP {second_reg}")
          self.calculate_expression(expression[2], target_reg, third_reg)
          self.assembly.append(f"SWAP {target_reg}")
          self.assembly.append(f"ADD {second_reg}")
          self.assembly.append(f"SWAP {target_reg}")
      elif expression[0] == "minus":
        if expression[1][0] == expression[2][0] == "const":
          value = expression[1][1] - expression[2][1]
          if value:
            self.prepare_const(value, target_reg)
          else:
            self.assembly.append(f"RESET {target_reg}")
        elif expression[1] == expression[2]:
          self.assembly.append(f"RESET {target_reg}")
        elif const and const == 1 and expression[const][1] == 0:
          self.assembly.append(f"RESET {target_reg}")
        else:
          self.calculate_expression(expression[1], second_reg, third_reg)
          self.calculate_expression(expression[2], target_reg, third_reg)
          self.assembly.append(f"SWAP {second_reg}")
          self.assembly.append(f"SUB {second_reg}")
          self.assembly.append(f"SWAP {target_reg}")
      elif expression[0] == "times":
        if expression[1][0] == expression[2][0] == "const":
          self.prepare_const(expression[1][1] * expression[2][1], target_reg)
          return
        if const:
          value = expression[const][1]
          if value == 0:
            self.assembly.append(f"RESET {target_reg}")
            return
          elif value == 1:
            self.calculate_expression(expression[variable], target_reg, second_reg)
            return
          elif value & (value - 1) == 0:
            self.calculate_expression(expression[variable], target_reg, second_reg)
            self.assembly.append(f"SWAP {target_reg}")
            while value > 1:
              self.assembly.append(f"ADD a")
              value /= 2
            self.assembly.append(f"SWAP {target_reg}")
            return
        if expression[1] == expression[2]:
          self.calculate_expression(expression[1], second_reg, third_reg)
          self.assembly.append(f"RESET {third_reg}")
          self.assembly.append(f"SWAP {third_reg}")
          self.assembly.append(f"ADD {second_reg}")
          self.assembly.append(f"SWAP {third_reg}")
        else:
          self.calculate_expression(expression[1], second_reg, fourth_reg)
          self.calculate_expression(expression[2], third_reg, fourth_reg)
        self.assembly.append(f"RESET a")
        self.assembly.append(f"RESET {fourth_reg}")
        self.assembly.append(f"RESET {fifth_reg}")
        self.assembly.append(f"RESET {sixth_reg}")
        self.assembly.append(f"RESET {seventh_reg}")
        self.assembly.append(f"RESET {eighth_reg}")
        self.assembly.append(f"INC {fifth_reg}")
        self.assembly.append(f"DEC {sixth_reg}")
        self.assembly.append(f"SWAP {second_reg}")
        self.assembly.append(f"JZERO 49")
        self.assembly.append(f"SWAP {second_reg}")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"JZERO -3")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {second_reg}")
        self.assembly.append(f"JPOS 5")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"SUB {second_reg}")
        self.assembly.append(f"SWAP {second_reg}")
        self.assembly.append(f"INC {seventh_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {third_reg}")
        self.assembly.append(f"JPOS 5")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"SUB {third_reg}")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"DEC {seventh_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"JZERO 22")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"RESET {eighth_reg}")
        self.assembly.append(f"SWAP {eighth_reg}")
        self.assembly.append(f"ADD {third_reg}")
        self.assembly.append(f"SHIFT {sixth_reg}")
        self.assembly.append(f"SHIFT {fifth_reg}")
        self.assembly.append(f"SUB {third_reg}")
        self.assembly.append(f"JNEG 3")
        self.assembly.append(f"SWAP {eighth_reg}")
        self.assembly.append(f"JUMP 5")
        self.assembly.append(f"SWAP {eighth_reg}")
        self.assembly.append(f"SWAP {fourth_reg}")
        self.assembly.append(f"ADD {second_reg}")
        self.assembly.append(f"SWAP {fourth_reg}")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"SHIFT {sixth_reg}")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"SWAP {second_reg}")
        self.assembly.append(f"SHIFT {fifth_reg}")
        self.assembly.append(f"SWAP {second_reg}")
        self.assembly.append(f"JUMP -23")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {seventh_reg}")
        self.assembly.append(f"JZERO 4")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"SUB {fourth_reg}")
        self.assembly.append(f"JUMP 2")
        self.assembly.append(f"SWAP {fourth_reg}")
        self.assembly.append(f"SWAP {target_reg}")
      elif expression[0] == "div":
        if expression[1][0] == expression[2][0] == "const":
          if expression[2][1] > 0:
            self.prepare_const(expression[1][1] // expression[2][1], target_reg)
          else:
            self.assembly.append(f"RESET {target_reg}")
          return
        elif expression[1] == expression[2]:
          self.calculate_expression(expression[1], third_reg, second_reg)
          self.assembly.append(f"SWAP {third_reg}")
          self.assembly.append(f"JZERO 3")
          self.assembly.append(f"RESET {target_reg}")
          self.assembly.append(f"INC {target_reg}")
          return
        elif const and const == 1 and expression[const][1] == 0:
          self.assembly.append(f"RESET {target_reg}")
          return
        elif const and const == 2:
          value = expression[const][1]
          if value == 0:
            self.assembly.append(f"RESET {target_reg}")
            return
          elif value == 1:
            self.calculate_expression(expression[variable], target_reg, second_reg)
            return
          elif value & (value - 1) == 0:
            self.calculate_expression(expression[variable], target_reg, second_reg)
            while value > 1:
              self.assembly.append(f"RESET h")
              self.assembly.append(f"DEC h")
              self.assembly.append(f"SWAP {target_reg}")
              self.assembly.append(f"SHIFT h")
              self.assembly.append(f"SWAP {target_reg}")
              value /= 2
            return
        self.calculate_expression(expression[1], fourth_reg, second_reg)
        self.calculate_expression(expression[2], fifth_reg, second_reg)
        self.assembly.append(f"RESET {second_reg}")
        self.assembly.append(f"RESET {third_reg}")
        self.assembly.append(f"SWAP {fourth_reg}")
        self.assembly.append(f"JZERO 3")
        self.assembly.append(f"SWAP {fourth_reg}")
        self.assembly.append(f"SWAP {fifth_reg}")
        self.assembly.append(f"JZERO 76")
        self.assembly.append(f"SWAP {fifth_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {fourth_reg}")
        self.assembly.append(f"JPOS 11")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"SUB {fourth_reg}")
        self.assembly.append(f"SWAP {fourth_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {fifth_reg}")
        self.assembly.append(f"JPOS 11")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"SUB {fifth_reg}")
        self.assembly.append(f"SWAP {fifth_reg}")
        self.assembly.append(f"JUMP 8")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {fifth_reg}")
        self.assembly.append(f"JPOS 5")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"SUB {fifth_reg}")
        self.assembly.append(f"SWAP {fifth_reg}")
        self.assembly.append(f"JUMP 58")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {fourth_reg}")
        self.assembly.append(f"RESET {seventh_reg}")
        self.assembly.append(f"DEC {third_reg}")
        self.assembly.append(f"JZERO 4")
        self.assembly.append(f"SHIFT {third_reg}")
        self.assembly.append(f"INC {seventh_reg}")
        self.assembly.append(f"JUMP -3")
        self.assembly.append(f"INC {third_reg}")
        self.assembly.append(f"SWAP {seventh_reg}")
        self.assembly.append(f"JNEG 44")
        self.assembly.append(f"SWAP {seventh_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {fourth_reg}")
        self.assembly.append(f"SWAP {sixth_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {seventh_reg}")
        self.assembly.append(f"JZERO 9")
        self.assembly.append(f"SWAP {eighth_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"SWAP {sixth_reg}")
        self.assembly.append(f"DEC {sixth_reg}")
        self.assembly.append(f"SHIFT {sixth_reg}")
        self.assembly.append(f"SWAP {sixth_reg}")
        self.assembly.append(f"ADD {eighth_reg}")
        self.assembly.append(f"JUMP -8")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"INC a")
        self.assembly.append(f"SWAP {second_reg}")
        self.assembly.append(f"SHIFT {second_reg}")
        self.assembly.append(f"SWAP {second_reg}")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"SHIFT {third_reg}")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {sixth_reg}")
        self.assembly.append(f"RESET {eighth_reg}")
        self.assembly.append(f"DEC {eighth_reg}")
        self.assembly.append(f"SHIFT {eighth_reg}")
        self.assembly.append(f"INC {eighth_reg}")
        self.assembly.append(f"INC {eighth_reg}")
        self.assembly.append(f"SHIFT {eighth_reg}")
        self.assembly.append(f"SUB {sixth_reg}")
        self.assembly.append(f"JZERO 2")
        self.assembly.append(f"INC {third_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {third_reg}")
        self.assembly.append(f"SUB {fifth_reg}")
        self.assembly.append(f"JNEG 3")
        self.assembly.append(f"INC {second_reg}")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"DEC {seventh_reg}")
        self.assembly.append(f"JUMP -44")
        self.assembly.append(f"SWAP {second_reg}")
        self.assembly.append(f"JUMP 58")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {fourth_reg}")
        self.assembly.append(f"RESET {seventh_reg}")
        self.assembly.append(f"DEC {third_reg}")
        self.assembly.append(f"JZERO 4")
        self.assembly.append(f"SHIFT {third_reg}")
        self.assembly.append(f"INC {seventh_reg}")
        self.assembly.append(f"JUMP -3")
        self.assembly.append(f"INC {third_reg}")
        self.assembly.append(f"SWAP {seventh_reg}")
        self.assembly.append(f"JNEG 44")
        self.assembly.append(f"SWAP {seventh_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {fourth_reg}")
        self.assembly.append(f"SWAP {sixth_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {seventh_reg}")
        self.assembly.append(f"JZERO 9")
        self.assembly.append(f"SWAP {eighth_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"SWAP {sixth_reg}")
        self.assembly.append(f"DEC {sixth_reg}")
        self.assembly.append(f"SHIFT {sixth_reg}")
        self.assembly.append(f"SWAP {sixth_reg}")
        self.assembly.append(f"ADD {eighth_reg}")
        self.assembly.append(f"JUMP -8")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"INC a")
        self.assembly.append(f"SWAP {second_reg}")
        self.assembly.append(f"SHIFT {second_reg}")
        self.assembly.append(f"SWAP {second_reg}")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"SHIFT {third_reg}")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {sixth_reg}")
        self.assembly.append(f"RESET {eighth_reg}")
        self.assembly.append(f"DEC {eighth_reg}")
        self.assembly.append(f"SHIFT {eighth_reg}")
        self.assembly.append(f"INC {eighth_reg}")
        self.assembly.append(f"INC {eighth_reg}")
        self.assembly.append(f"SHIFT {eighth_reg}")
        self.assembly.append(f"SUB {sixth_reg}")
        self.assembly.append(f"JZERO 2")
        self.assembly.append(f"INC {third_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {third_reg}")
        self.assembly.append(f"SUB {fifth_reg}")
        self.assembly.append(f"JNEG 3")
        self.assembly.append(f"INC {second_reg}")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"DEC {seventh_reg}")
        self.assembly.append(f"JUMP -44")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"SUB {second_reg}")
        self.assembly.append(f"DEC a")
        self.assembly.append(f"SWAP {target_reg}")
      elif expression[0] == "mod":
        if expression[1][0] == expression[2][0] == "const":
          self.prepare_const(expression[1][1] % expression[2][1], target_reg)
          return
        elif expression[1] == expression[2]:
          self.assembly.append(f"RESET {target_reg}")
          return
        self.calculate_expression(expression[1], fourth_reg, second_reg)
        self.calculate_expression(expression[2], fifth_reg, second_reg)
        self.assembly.append(f"RESET {second_reg}")
        self.assembly.append(f"RESET {third_reg}")
        self.assembly.append(f"SWAP {fourth_reg}")
        self.assembly.append(f"JZERO 3")
        self.assembly.append(f"SWAP {fourth_reg}")
        self.assembly.append(f"SWAP {fifth_reg}")
        self.assembly.append(f"JZERO 84")
        self.assembly.append(f"SWAP {fifth_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {fourth_reg}")
        self.assembly.append(f"ADD {fifth_reg}")
        self.assembly.append(f"JZERO -5")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {fourth_reg}")
        self.assembly.append(f"JPOS 12")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"SUB {fourth_reg}")
        self.assembly.append(f"SWAP {fourth_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {fifth_reg}")
        self.assembly.append(f"JPOS 12")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"INC {second_reg}")
        self.assembly.append(f"SUB {fifth_reg}")
        self.assembly.append(f"SWAP {fifth_reg}")
        self.assembly.append(f"JUMP 9")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {fifth_reg}")
        self.assembly.append(f"JPOS 6")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"INC {second_reg}")
        self.assembly.append(f"SUB {fifth_reg}")
        self.assembly.append(f"SWAP {fifth_reg}")
        self.assembly.append(f"JUMP 60")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {fourth_reg}")
        self.assembly.append(f"RESET {seventh_reg}")
        self.assembly.append(f"DEC {third_reg}")
        self.assembly.append(f"JZERO 4")
        self.assembly.append(f"SHIFT {third_reg}")
        self.assembly.append(f"INC {seventh_reg}")
        self.assembly.append(f"JUMP -3")
        self.assembly.append(f"INC {third_reg}")
        self.assembly.append(f"SWAP {seventh_reg}")
        self.assembly.append(f"JNEG 40")
        self.assembly.append(f"SWAP {seventh_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {fourth_reg}")
        self.assembly.append(f"SWAP {sixth_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {seventh_reg}")
        self.assembly.append(f"JZERO 9")
        self.assembly.append(f"SWAP {eighth_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"SWAP {sixth_reg}")
        self.assembly.append(f"DEC {sixth_reg}")
        self.assembly.append(f"SHIFT {sixth_reg}")
        self.assembly.append(f"SWAP {sixth_reg}")
        self.assembly.append(f"ADD {eighth_reg}")
        self.assembly.append(f"JUMP -8")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"INC a")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"SHIFT {third_reg}")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {sixth_reg}")
        self.assembly.append(f"RESET {eighth_reg}")
        self.assembly.append(f"DEC {eighth_reg}")
        self.assembly.append(f"SHIFT {eighth_reg}")
        self.assembly.append(f"INC {eighth_reg}")
        self.assembly.append(f"INC {eighth_reg}")
        self.assembly.append(f"SHIFT {eighth_reg}")
        self.assembly.append(f"SUB {sixth_reg}")
        self.assembly.append(f"JZERO 2")
        self.assembly.append(f"INC {third_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {third_reg}")
        self.assembly.append(f"SUB {fifth_reg}")
        self.assembly.append(f"JNEG 3")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"DEC {seventh_reg}")
        self.assembly.append(f"JUMP -40")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"SWAP {second_reg}")
        self.assembly.append(f"JZERO 4")
        self.assembly.append(f"DEC a")
        self.assembly.append(f"SUB {second_reg}")
        self.assembly.append(f"SWAP {second_reg}")
        self.assembly.append(f"SWAP {second_reg}")
        self.assembly.append(f"JUMP 61")
        self.assembly.append(f"JUMP -1")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {fourth_reg}")
        self.assembly.append(f"RESET {seventh_reg}")
        self.assembly.append(f"DEC {third_reg}")
        self.assembly.append(f"JZERO 4")
        self.assembly.append(f"SHIFT {third_reg}")
        self.assembly.append(f"INC {seventh_reg}")
        self.assembly.append(f"JUMP -3")
        self.assembly.append(f"INC {third_reg}")
        self.assembly.append(f"SWAP {seventh_reg}")
        self.assembly.append(f"JNEG 40")
        self.assembly.append(f"SWAP {seventh_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {fourth_reg}")
        self.assembly.append(f"SWAP {sixth_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {seventh_reg}")
        self.assembly.append(f"JZERO 9")
        self.assembly.append(f"SWAP {eighth_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"SWAP {sixth_reg}")
        self.assembly.append(f"DEC {sixth_reg}")
        self.assembly.append(f"SHIFT {sixth_reg}")
        self.assembly.append(f"SWAP {sixth_reg}")
        self.assembly.append(f"ADD {eighth_reg}")
        self.assembly.append(f"JUMP -8")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"INC a")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"SHIFT {third_reg}")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {sixth_reg}")
        self.assembly.append(f"RESET {eighth_reg}")
        self.assembly.append(f"DEC {eighth_reg}")
        self.assembly.append(f"SHIFT {eighth_reg}")
        self.assembly.append(f"INC {eighth_reg}")
        self.assembly.append(f"INC {eighth_reg}")
        self.assembly.append(f"SHIFT {eighth_reg}")
        self.assembly.append(f"SUB {sixth_reg}")
        self.assembly.append(f"JZERO 2")
        self.assembly.append(f"INC {third_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"ADD {third_reg}")
        self.assembly.append(f"SUB {fifth_reg}")
        self.assembly.append(f"JNEG 3")
        self.assembly.append(f"SWAP {third_reg}")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"DEC {seventh_reg}")
        self.assembly.append(f"JUMP -40")
        self.assembly.append(f"RESET a")
        self.assembly.append(f"SUB {third_reg}")
        self.assembly.append(f"ADD {fifth_reg}")
        self.assembly.append(f"SWAP {second_reg}")
        self.assembly.append(f"JZERO 4")
        self.assembly.append(f"DEC a")
        self.assembly.append(f"SUB {second_reg}")
        self.assembly.append(f"SWAP {second_reg}")
        self.assembly.append(f"SWAP {second_reg}")
        self.assembly.append(f"SWAP {target_reg}")

  def check_condition(self, condition, target_reg='a', second_reg='b', third_reg='c'):
    self.calculate_expression(condition[1], third_reg, second_reg)
    self.calculate_expression(condition[2], second_reg, target_reg)
    if condition[0] == "leq":
      self.assembly.append(f"SWAP {second_reg}")
      self.assembly.append(f"SUB {third_reg}")
      self.assembly.append(f"JNEG finish")
    elif condition[0] == "geq":
      self.assembly.append(f"SWAP {second_reg}")
      self.assembly.append(f"SUB {third_reg}")
      self.assembly.append(f"JPOS finish")
    elif condition[0] == "le":
      self.assembly.append(f"SWAP {third_reg}")
      self.assembly.append(f"SUB {second_reg}")
      self.assembly.append(f"JZERO finish")
      self.assembly.append(f"JPOS finish")
    elif condition[0] == "ge":
      self.assembly.append(f"SWAP {third_reg}")
      self.assembly.append(f"SUB {second_reg}")
      self.assembly.append(f"JZERO finish")
      self.assembly.append(f"JNEG finish")
    elif condition[0] == "eq":
      self.assembly.append(f"SWAP {third_reg}")
      self.assembly.append(f"SUB {second_reg}")
      self.assembly.append(f"JZERO 2")
      self.assembly.append(f"JUMP finish")
    elif condition[0] == "neq":
      self.assembly.append(f"SWAP {third_reg}")
      self.assembly.append(f"SUB {second_reg}")
      self.assembly.append(f"JZERO finish")

  def load_array_at(self, array, index, target_reg, second_reg):
    self.load_array_address_at(array, index, target_reg, second_reg)
    self.assembly.append(f"LOAD {target_reg}")
    self.assembly.append(f"SWAP {target_reg}")
    
  def load_variable_at(self, array, target_reg, second_reg):
    variable = self.memory.get_variable(array)
    self.prepare_const(variable.memory_offset - variable.first_index, target_reg)
    self.assembly.append(f"SWAP {target_reg}")
    self.assembly.append(f"ADD {second_reg}")
    self.assembly.append(f"SWAP {target_reg}")

  def load_array_address_at(self, array, index, target_reg, second_reg):
    if type(index) == int:
      address = self.memory.get_address((array, index))
      self.prepare_const(address, target_reg)
    elif type(index) == tuple:
      if type(index[1]) == tuple:
        if index[1][0] == "undeclared":
          address = self.memory.get_address(index[1][1])
          self.prepare_const(address, second_reg)
          self.assembly.append(f"SWAP {second_reg}")
          self.assembly.append(f"LOAD a")
          self.assembly.append(f"SWAP {second_reg}")
          self.load_variable_at(array, target_reg, second_reg)
          return
        else:
          self.load_variable(index[1][1], second_reg, declared=False)
      else:
        if not self.memory[index[1]].initialized:
          raise Exception(f"Próba użycia {array}({index[1]}) gdzie zmienna {index[1]} nie jest zainicjalizowana")
        self.load_variable(index[1], second_reg)
        self.load_variable_at(array, target_reg, second_reg)
        return
      variable = self.memory.get_variable(array)
      self.prepare_const(variable.memory_offset - variable.first_index, target_reg)
      self.assembly.append(f"SWAP {target_reg}")
      self.assembly.append(f"ADD {second_reg}")
      self.assembly.append(f"SWAP {target_reg}")

  def load_variable(self, pidentifier, target_reg, declared=True):
    if not declared and self.iterators and pidentifier == self.iterators[-1]:
      self.assembly.append(f"RESET {target_reg}")
      self.assembly.append(f"SWAP f")
      self.assembly.append(f"ADD {target_reg}")
      self.assembly.append(f"SWAP f")
    else:
      self.load_variable_address(pidentifier, target_reg, declared)
      self.assembly.append(f"LOAD {target_reg}")
      self.assembly.append(f"SWAP {target_reg}")

  def load_variable_address(self, pidentifier, target_reg, declared=True):
    if declared or pidentifier in self.iterators:
      address = self.memory.get_address(pidentifier)
      self.prepare_const(address, target_reg)
      if self.iterators and pidentifier == self.iterators[-1]:
        self.assembly.append(f"STORE {target_reg}")
    else:
      raise Exception(f"Niezadeklarowana zmienna {pidentifier}")

  def prepare_const(self, const, target_reg='a'):
    self.assembly.append(f"RESET {target_reg}")
    self.assembly.append(f"SWAP {target_reg}")
    if const > 0:
      bits = bin(const)[2:]
      for bit in bits[:-1]:
        if bit == '1':
          self.assembly.append(f"INC a")
        self.assembly.append(f"ADD a")
      if bits[-1] == '1':
        self.assembly.append(f"INC a")
    elif const < 0:
      const = -const
      bits = bin(const)[2:]
      for bit in bits[:-1]:
        if bit == '1':
          self.assembly.append(f"INC a")
        self.assembly.append(f"ADD a")
      if bits[-1] == '1':
        self.assembly.append(f"INC a")
      self.assembly.append(f"RESET h")
      self.assembly.append(f"SWAP h")
      self.assembly.append(f"SUB h")
      self.assembly.append(f"RESET h")
    self.assembly.append(f"SWAP {target_reg}")

  def prepare_consts(self, consts, first_reg='b', second_reg='c'):
    for c in consts:
      address = self.memory.get_const(c)
      if address is None:
        address = self.memory.set_const(c)
        self.prepare_const(address, second_reg)
        self.prepare_const(c, first_reg)
        self.assembly.append(f"SWAP {first_reg}")
        self.assembly.append(f"STORE {second_reg}")

  def remove_prepared_consts(self, consts):
    for i in consts:
      self.memory.consts.pop(i)
      self.memory.memory_offset -= 1
