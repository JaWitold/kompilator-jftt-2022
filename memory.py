class MemoryCell:
  def __init__(self, memory_offset):
    self.memory_offset = memory_offset

class Variable(MemoryCell):
  def __init__(self, memory_offset):
    super().__init__(memory_offset)
    self.initialized = False

class Array(MemoryCell):
  def __init__(self, pidentifier, memory_offset, first_index, last_index):
    super().__init__(memory_offset)
    self.pidentifier = pidentifier
    self.first_index = first_index
    self.last_index = last_index

  def get_at(self, index):
    if self.first_index <= index <= self.last_index:
      return self.memory_offset - self.first_index + index
    else:
      raise Exception(f"Indeks {index} jest poza zakresem {self.pidentifier}[{self.first_index}:{self.last_index}]")

class Iterator(MemoryCell):
  def __init__(self, memory_offset, limit_address):
    super().__init__(memory_offset)
    self.limit_address = limit_address

class Memory(dict):
  def __init__(self):
    super().__init__()
    self.memory_offset = 0
    self.consts = {}
    self.iterators = {}

  def set_variable(self, pidentifier):
    if pidentifier in self:
      raise Exception(f"Redeklaracja {pidentifier}")
    self.setdefault(pidentifier, Variable(self.memory_offset))
    self.memory_offset += 1

  def get_variable(self, pidentifier):
    if pidentifier in self:
      return self[pidentifier]
    elif pidentifier in self.iterators:
      return self.iterators[pidentifier]
    else:
      raise Exception(f"Niezadeklarowana zmienna {pidentifier}")

  def set_array(self, pidentifier, first_index, last_index):
    if pidentifier in self:
      raise Exception(f"Redeklaracja {pidentifier}")
    elif first_index > last_index:
      raise Exception(f"Niepoprawny zakres w tablicy {pidentifier}, {first_index} powinno być mniejsze lub równe {last_index}")
    self.setdefault(pidentifier, Array(pidentifier, self.memory_offset, first_index, last_index))
    self.memory_offset += last_index - first_index + 1

  def get_array_at(self, pidentifier, index):
    if pidentifier in self:
      try:
        return self[pidentifier].get_at(index)
      except AttributeError:
        raise Exception(f"Nie poprawne użycie {pidentifier} jako tablicy")
    else:
      raise Exception(f"Niezadeklarowana tablice {pidentifier}")

  def set_iterator(self, pidentifier):
    last_address = self.memory_offset
    iterator_address = self.memory_offset + 1
    self.iterators.setdefault(pidentifier, Iterator(iterator_address, last_address))
    self.memory_offset += 2
    return iterator_address, last_address

  def get_iterator(self, pidentifier):
    if pidentifier in self.iterators:
      iterator = self.iterators[pidentifier]
      return iterator.memory_offset, iterator.limit_address

  def set_const(self, value):
    const_address = self.memory_offset
    self.consts.setdefault(value, const_address)
    self.memory_offset += 1
    return const_address

  def get_const(self, value):
    if value in self.consts:
      return self.consts[value]

  def get_address(self, pidentifier):
    if type(pidentifier) == str:
      return self.get_variable(pidentifier).memory_offset
    else:
      return self.get_array_at(pidentifier[0], pidentifier[1])
