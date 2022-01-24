from parser import CompilerParser, CompilerLexer
import sys

source_file = sys.argv[1]
output_file = sys.argv[2]

lexer = CompilerLexer()
parser = CompilerParser()

with open(source_file, 'r') as line:
  text = line.read()

compiler = parser.parse(lexer.tokenize(text))
assembly = compiler.compile()

with open(output_file, 'w') as destination:
  for line in assembly:
    print(line, file = destination)
