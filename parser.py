from sly import Parser
from lexer import CompilerLexer
from memory import Memory, Array, Variable
from code_generator import CodeGenerator

class CompilerParser(Parser):
  tokens = CompilerLexer.tokens
  memory = Memory()
  consts = set()

  @_('VAR declarations BEGIN commands END', 'BEGIN commands END')
  def program(self, p):
     return CodeGenerator(p.commands, self.memory)

  @_('declarations "," PIDENTIFIER')
  def declarations(self, p):
    self.memory.add_variable(p[-1])

  @_('declarations "," PIDENTIFIER "[" NUMBER ":" NUMBER "]" ')
  def declarations(self, p):
    self.memory.set_array(p[2], p[4], p[6])

  @_('PIDENTIFIER')
  def declarations(self, p):
    self.memory.add_variable(p[-1])

  @_('PIDENTIFIER "[" NUMBER ":" NUMBER "]"')
  def declarations(self, p):
    self.memory.set_array(p[0], p[2], p[4])

  @_('commands command')
  def commands(self, p):
    return p[0] + [p[1]]

  @_('command')
  def commands(self, p):
    return [p[0]]

  @_('identifier ASSIGN expression ";"')
  def command(self, p):
    return "assign", p[0], p[2]

  @_('IF condition THEN commands ELSE commands ENDIF')
  def command(self, p):
    resp = "if_else", p[1], p[3], p[5], self.consts.copy()
    self.consts.clear()
    return resp

  @_('IF condition THEN commands ENDIF')
  def command(self, p):
    resp = "if", p[1], p[3], self.consts.copy()
    self.consts.clear()
    return resp

  @_('WHILE condition DO commands ENDWHILE')
  def command(self, p):
    resp = "while", p[1], p[3], self.consts.copy()
    self.consts.clear()
    return resp

  @_('REPEAT commands UNTIL condition ";"')
  def command(self, p):
    return "repeat", p[3], p[1]

  @_('FOR PIDENTIFIER FROM value TO value DO commands ENDFOR')
  def command(self, p):
    resp = "for_to", p[1], p[3], p[5], p[7], self.consts.copy()
    self.consts.clear()
    return resp

  @_('FOR PIDENTIFIER FROM value DOWNTO value DO commands ENDFOR')
  def command(self, p):
    resp = "for_down_to", p[1], p[3], p[5], p[7], self.consts.copy()
    self.consts.clear()
    return resp

  @_('READ identifier ";"')
  def command(self, p):
    return "read", p[1]

  @_('WRITE value ";"')
  def command(self, p):
    if p[1][0] == "const":
      self.consts.add(int(p[1][1]))
    return "write", p[1]

  @_('value')
  def expression(self, p):
    return p[0]

  @_('value PLUS value')
  def expression(self, p):
    return "plus", p[0], p[2]

  @_('value MINUS value')
  def expression(self, p):
    return "minus", p[0], p[2]

  @_('value TIMES value')
  def expression(self, p):
    return "times", p[0], p[2]

  @_('value DIV value')
  def expression(self, p):
    return "div", p[0], p[2]

  @_('value MOD value')
  def expression(self, p):
    return "mod", p[0], p[2]

  @_('value EQ value')
  def condition(self, p):
    return "eq", p[0], p[2]

  @_('value NEQ value')
  def condition(self, p):
    return "neq", p[0], p[2]

  @_('value LE value')
  def condition(self, p):
    return "le", p[0], p[2]

  @_('value GE value')
  def condition(self, p):
    return "ge", p[0], p[2]

  @_('value LEQ value')
  def condition(self, p):
    return "leq", p[0], p[2]

  @_('value GEQ value')
  def condition(self, p):
    return "geq", p[0], p[2]

  @_('NUMBER')
  def value(self, p):
    return "const", p[0]

  @_('identifier')
  def value(self, p):
    return "load", p[0]

  @_('PIDENTIFIER')
  def identifier(self, p):
    if p[0] in self.memory:
      return p[0]
    else:
      return "undeclared", p[0]

  @_('PIDENTIFIER "[" PIDENTIFIER "]"')
  def identifier(self, p):
    if p[0] in self.memory and type(self.memory[p[0]]) == Array:
      if p[2] in self.memory and type(self.memory[p[2]]) == Variable:
        return "array", p[0], ("load", p[2])
      else:
        return "array", p[0], ("load", ("undeclared", p[2]))
    else:
      raise Exception(f"Undeclared array {p[0]}")

  @_('PIDENTIFIER "[" NUMBER "]"')
  def identifier(self, p):
    if p[0] in self.memory and type(self.memory[p[0]]) == Array:
      return "array", p[0], p[2]
    else:
      raise Exception(f"Undeclared array {p[0]}")

  def error(self, token):
    raise Exception(f"Syntax error: '{token.value}'")
