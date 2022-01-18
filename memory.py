class Variable:
  def __init__(self, memory_offset):
    self.memory_offset = memory_offset
    self.initialized = False

class Array:
  def __init__(self, pidentifier, memory_offset, first_index, last_index):
    self.pidentifier = pidentifier
    self.memory_offset = memory_offset
    self.first_index = first_index
    self.last_index = last_index

  def get_at(self, index):
    if self.first_index <= index <= self.last_index:
      return self.memory_offset - self.first_index + index
    else:
      raise Exception(f"Index {index} out of range for array {self.pidentifier}")

class Iterator:
  def __init__(self, memory_offset, limit_address):
    self.memory_offset = memory_offset
    self.limit_address = limit_address

class Memory(dict):
  def __init__(self):
    super().__init__()
    self.memory_offset = 0
    self.consts = {}
    self.iterators = {}

  def add_variable(self, pidentifier):
    if pidentifier in self:
      raise Exception(f"Redeclaration of {pidentifier}")
    self.setdefault(pidentifier, Variable(self.memory_offset))
    self.memory_offset += 1

  def get_variable(self, pidentifier):
    if pidentifier in self:
      return self[pidentifier]
    elif pidentifier in self.iterators:
      return self.iterators[pidentifier]
    else:
      raise Exception(f"Undeclared variable {pidentifier}")

  def set_array(self, pidentifier, first_index, last_index):
    if pidentifier in self:
      raise Exception(f"Redeclaration of {pidentifier}")
    elif first_index > last_index:
      raise Exception(f"Wrong range in declaration of {pidentifier}")
    self.setdefault(pidentifier, Array(pidentifier, self.memory_offset, first_index, last_index))
    self.memory_offset += last_index - first_index + 1

  def get_array_at(self, pidentifier, index):
    if pidentifier in self:
      try:
        return self[pidentifier].get_at(index)
      except AttributeError:
        raise Exception(f"Non-array {pidentifier} used as an array")
    else:
      raise Exception(f"Undeclared array {pidentifier}")

  def set_iterator(self, pidentifier):
    last_address = self.memory_offset
    self.memory_offset += 1
    self.iterators.setdefault(pidentifier, Iterator(self.memory_offset, last_address))
    self.memory_offset += 1
    return self.memory_offset - 1, last_address

  def get_iterator(self, pidentifier):
    if pidentifier in self.iterators:
      iterator = self.iterators[pidentifier]
      return iterator.memory_offset, iterator.limit_address

  def set_const(self, value):
    self.consts.setdefault(value, self.memory_offset)
    self.memory_offset += 1
    return self.memory_offset - 1

  def get_const(self, value):
    if value in self.consts:
      return self.consts[value]

  def get_address(self, pidentifier):
    if type(pidentifier) == str:
      return self.get_variable(pidentifier).memory_offset
    else:
      return self.get_array_at(pidentifier[0], pidentifier[1])
