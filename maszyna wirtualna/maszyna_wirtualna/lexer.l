/*
 * Lexer interpretera maszyny wirtualnej do projektu z JFTT2021
 *
 * Autor: Maciek Gębala
 * http://ki.pwr.edu.pl/gebala/
 * 2021-11-12
*/
%option noyywrap
%option yylineno
%option nounput
%{
#include "parser.hh"
#include "instructions.hh"

int yylex();
%}
%%
\(([^\)]|\n)*\) ;
[ \t]+          ;
GET             { yylval = GET;   return COM_0; };
PUT             { yylval = PUT;   return COM_0; };
LOAD            { yylval = LOAD;  return COM_1; };
STORE           { yylval = STORE; return COM_1; };
ADD             { yylval = ADD;   return COM_1; };
SUB             { yylval = SUB;   return COM_1; };
SHIFT           { yylval = SHIFT; return COM_1; };
SWAP            { yylval = SWAP;  return COM_1; };
RESET           { yylval = RESET;  return COM_1; };
INC             { yylval = INC;   return COM_1; };
DEC             { yylval = DEC;   return COM_1; };
JUMP            { yylval = JUMP;  return JUMP_1; };
JPOS            { yylval = JPOS;  return JUMP_1; };
JZERO           { yylval = JZERO; return JUMP_1; };
JNEG            { yylval = JNEG;  return JUMP_1; };
HALT            { yylval = HALT;  return STOP; };
a               { yylval = 0;     return REG; };
b               { yylval = 1;     return REG; };
c               { yylval = 2;     return REG; };
d               { yylval = 3;     return REG; };
e               { yylval = 4;     return REG; };
f               { yylval = 5;     return REG; };
g               { yylval = 6;     return REG; };
h               { yylval = 7;     return REG; };
\-?[1-9][0-9]*  { yylval = atoi( yytext );  return LABEL; };
\n              ;
.               return ERROR;
%%
