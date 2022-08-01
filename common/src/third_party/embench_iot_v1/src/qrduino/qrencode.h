/* BEEBS qrduino benchmark

   This version, copyright (C) 2014-2019 Embecosm Limited and University of
   Bristol

   Contributor James Pallister <james.pallister@bristol.ac.uk>
   Contributor Jeremy Bennett <jeremy.bennett@embecosm.com>

   This file is part of Embench and was formerly part of the Bristol/Embecosm
   Embedded Benchmark Suite.

   SPDX-License-Identifier: GPL-3.0-or-later

   Original code from: https://github.com/tz1/qrduino */

#define PROGMEM
#define memcpy_P memcpy
#define __LPM(x) *x
#define pgm_read_word(x) *x

// malloc-ed by initframe, free manually
extern unsigned char *strinbuf;	// string iput buffer
extern unsigned char *qrframe;
// setup the base frame structure - can be reused
void initframe (void);
// free the basic frame malloced structures
void freeframe (void);
// these resturn maximum string size to send in
unsigned initeccsize (unsigned char ecc, unsigned size);
unsigned initecc (unsigned char level, unsigned char version);

extern unsigned char WD, WDB;
#include "qrbits.h"

// strinbuf in, qrframe out
void qrencode (void);

void freeecc ();


/*
   Local Variables:
   mode: C
   c-file-style: "gnu"
   End:
*/
