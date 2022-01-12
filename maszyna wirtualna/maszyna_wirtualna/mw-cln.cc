/*
 * Kod interpretera maszyny rejestrowej do projektu z JFTT2021
 *
 * Autor: Maciek Gębala
 * http://ki.pwr.edu.pl/gebala/
 * 2021-11-12
 * (wersja cln)
*/
#include <iostream>

#include <utility>
#include <vector>
#include <map>

#include <cstdlib> 	// rand()
#include <ctime>

#include <cln/cln.h>

#include "instructions.hh"
#include "colors.hh"

using namespace std;
using namespace cln;

void run_machine( vector< pair<int,int> > & program )
{
  map<cl_I,cl_I> pam;

  cl_I r[8];
  int lr;

  cl_I t, io, tmp;
  bool error=false;

  cout << cBlue << "Uruchamianie programu." << cReset << endl;
  lr = 0;
  srand( time(NULL) );
  for(int i = 0; i<8; i++ ) r[i] = rand();
  t = 0;
  io = 0;
  while( program[lr].first!=HALT )	// HALT
  {
    switch( program[lr].first )
    {
      case GET:	cout << "? "; cin >> r[0]; io+=100; lr++; break;
      case PUT:	cout << "> " << r[0] << endl; io+=100; lr++; break;

      case LOAD:	if(r[program[lr].second]<0) error=true; r[0] = pam[r[program[lr].second]]; t+=50; lr++; break;
      case STORE:	if(r[program[lr].second]<0) error=true; pam[r[program[lr].second]] = r[0]; t+=50; lr++; break;

      case ADD:	r[0] += r[program[lr].second]; t+=10; lr++; break;
      case SUB:	r[0] -= r[program[lr].second]; t+=10; lr++; break;
      case SHIFT:	if( r[program[lr].second] >= 0 ) r[0] <<= r[program[lr].second]; else r[0] >>= -r[program[lr].second]; t+=5; lr++; break;

      case SWAP:	tmp = r[program[lr].second]; r[program[lr].second] = r[0]; r[0] = tmp; t+=1; lr++; break;
      case RESET:	r[program[lr].second] = 0; t+=1; lr++; break;
      case INC:	r[program[lr].second]++; t+=1; lr++; break;
      case DEC:	r[program[lr].second]--; t+=1; lr++; break;

      case JUMP: 	lr += program[lr].second; t+=1; break;
      case JPOS:	if( r[0]>0 ) lr += program[lr].second; else lr++; t+=1; break;
      case JZERO:	if( r[0]==0 ) lr += program[lr].second; else lr++; t+=1; break;
      case JNEG:	if( r[0]<0 ) lr += program[lr].second; else lr++; t+=1; break;
      default: break;
    }
    if( error )
    {
      cerr << cRed << "Błąd: ujemny adres pamięci." << cReset << endl;
      exit(-1);
    }
    if( lr<0 || lr>=(int)program.size() )
    {
      cerr << cRed << "Błąd: Wywołanie nieistniejącej instrukcji nr " << lr << "." << cReset << endl;
      exit(-1);
    }
  }
  cout << cBlue << "Skończono program (koszt: " << (t+io) << "; w tym i/o: " << io << ")." << cReset << endl;
}
