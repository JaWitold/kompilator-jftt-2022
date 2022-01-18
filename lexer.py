from sly import Lexer

class CompilerLexer(Lexer):
  tokens = {VAR, BEGIN, END, PIDENTIFIER, NUMBER, IF, THEN, ELSE, ENDIF, WHILE, DO, ENDWHILE, REPEAT, UNTIL, FOR, FROM, TO, DOWNTO, ENDFOR, READ, WRITE, EQ, NEQ, GE, LE, GEQ, LEQ, ASSIGN, PLUS, MINUS, TIMES, DIV, MOD}
  literals = {',', ':', ';', '[', ']'}
  ignore = ' \t'

  @_(r'\([^\)]*\)')
  def comment(self, t):
    self.lineno += t.value.count('\n')

  @_(r'\n+')
  def newline(self, t):
    self.lineno += len(t.value)

  VAR         = r"VAR"
  BEGIN       = r"BEGIN"
  ENDWHILE    = r"ENDWHILE"
  ENDFOR      = r"ENDFOR"
  ENDIF       = r"ENDIF"
  END         = r"END"
  WHILE       = r"WHILE"
  FOR         = r"FOR"
  IF          = r"IF"
  THEN        = r"THEN"
  ELSE        = r"ELSE"
  DOWNTO      = r"DOWNTO"
  DO          = r"DO"
  TO          = r"TO"
  FROM        = r"FROM"
  REPEAT      = r"REPEAT"
  UNTIL       = r"UNTIL"
  READ        = r"READ"
  WRITE       = r"WRITE"
  ASSIGN      = r"ASSIGN"
  NEQ         = r"NEQ"
  GEQ         = r"GEQ"
  LEQ         = r"LEQ"
  EQ          = r"EQ"
  GE          = r"GE"
  LE          = r"LE"
  PIDENTIFIER = r"[_a-z]+"
  PLUS        = r'PLUS'
  MINUS       = r'MINUS'
  TIMES       = r'TIMES'
  DIV         = r'DIV'
  MOD         = r'MOD'

  @_(r'[-]?\d+')
  def NUMBER(self, t):
    t.value = int(t.value)
    return t

  def error(self, t):
    raise Exception(f"Illegal character '{t.value[0]}'")
