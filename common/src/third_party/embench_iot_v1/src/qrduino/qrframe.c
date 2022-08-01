/* BEEBS qrduino benchmark

   This version, copyright (C) 2014-2019 Embecosm Limited and University of
   Bristol

   Contributor James Pallister <james.pallister@bristol.ac.uk>
   Contributor Jeremy Bennett <jeremy.bennett@embecosm.com>

   This file is part of Embench and was formerly part of the Bristol/Embecosm
   Embedded Benchmark Suite.

   SPDX-License-Identifier: GPL-3.0-or-later

   Original code from: https://github.com/tz1/qrduino */

#include <string.h>
#include <stdlib.h>

/* Header for BEEBS library calls */

#include "third_party/embench_iot_v1/support/beebsc.h"

#ifndef __AVR__
#define PROGMEM
#define memcpy_P memcpy
#define __LPM(x) *x
#define pgm_read_word(x) *x
#else
#include <avr/pgmspace.h>
#endif

unsigned char *framebase;
unsigned char *framask;
unsigned char *rlens;
unsigned char VERSION;
unsigned char WD, WDB;		// filled in from verison by initframe

#define QRBIT(x,y) ( ( framebase[((x)>>3) + (y) * WDB] >> (7-((x) & 7 ))) & 1 )
#define SETQRBIT(x,y) framebase[((x)>>3) + (y) * WDB] |= 0x80 >> ((x) & 7)

static void
setmask (unsigned char x, unsigned char y)
{
  unsigned bt;
  if (x > y)
    {
      bt = x;
      x = y;
      y = bt;
    }
  // y*y = 1+3+5...
  bt = y;
  bt *= y;
  bt += y;
  bt >>= 1;
  bt += x;
  framask[bt >> 3] |= 0x80 >> (bt & 7);
}

static void
putfind ()
{
  unsigned char j, i, k, t;
  for (t = 0; t < 3; t++)
    {
      k = 0;
      i = 0;
      if (t == 1)
	k = (WD - 7);
      if (t == 2)
	i = (WD - 7);
      SETQRBIT (i + 3, k + 3);
      for (j = 0; j < 6; j++)
	{
	  SETQRBIT (i + j, k);
	  SETQRBIT (i, k + j + 1);
	  SETQRBIT (i + 6, k + j);
	  SETQRBIT (i + j + 1, k + 6);
	}
      for (j = 1; j < 5; j++)
	{
	  setmask (i + j, k + 1);
	  setmask (i + 1, k + j + 1);
	  setmask (i + 5, k + j);
	  setmask (i + j + 1, k + 5);
	}
      for (j = 2; j < 4; j++)
	{
	  SETQRBIT (i + j, k + 2);
	  SETQRBIT (i + 2, k + j + 1);
	  SETQRBIT (i + 4, k + j);
	  SETQRBIT (i + j + 1, k + 4);
	}
    }
}

static void
putalign (int x, int y)
{
  int j;

  SETQRBIT (x, y);
  for (j = -2; j < 2; j++)
    {
      SETQRBIT (x + j, y - 2);
      SETQRBIT (x - 2, y + j + 1);
      SETQRBIT (x + 2, y + j);
      SETQRBIT (x + j + 1, y + 2);
    }
  for (j = 0; j < 2; j++)
    {
      setmask (x - 1, y + j);
      setmask (x + 1, y - j);
      setmask (x - j, y - 1);
      setmask (x + j, y + 1);
    }
}

static const unsigned char adelta[41] PROGMEM = {
  0, 11, 15, 19, 23, 27, 31,	// force 1 pat
  16, 18, 20, 22, 24, 26, 28, 20, 22, 24, 24, 26, 28, 28, 22, 24, 24,
  26, 26, 28, 28, 24, 24, 26, 26, 26, 28, 28, 24, 26, 26, 26, 28, 28,
};

static void
doaligns (void)
{
  unsigned char delta, x, y;
  if (VERSION < 2)
    return;
  delta = __LPM (&adelta[VERSION]);
  y = WD - 7;
  for (;;)
    {
      x = WD - 7;
      while (x > delta - 3U)
	{
	  putalign (x, y);
	  if (x < delta)
	    break;
	  x -= delta;
	}
      if (y <= delta + 9U)
	break;
      y -= delta;
      putalign (6, y);
      putalign (y, 6);
    }
}

static const unsigned vpat[] PROGMEM = {
  0xc94, 0x5bc, 0xa99, 0x4d3, 0xbf6, 0x762, 0x847, 0x60d,
  0x928, 0xb78, 0x45d, 0xa17, 0x532, 0x9a6, 0x683, 0x8c9,
  0x7ec, 0xec4, 0x1e1, 0xfab, 0x08e, 0xc1a, 0x33f, 0xd75,
  0x250, 0x9d5, 0x6f0, 0x8ba, 0x79f, 0xb0b, 0x42e, 0xa64,
  0x541, 0xc69
};

static void
putvpat (void)
{
  unsigned char vers = VERSION;
  unsigned char x, y, bc;
  unsigned verinfo;
  if (vers < 7)
    return;
  verinfo = pgm_read_word (&vpat[vers - 7]);

  bc = 17;
  for (x = 0; x < 6; x++)
    for (y = 0; y < 3; y++, bc--)
      if (1 & (bc > 11 ? (unsigned) vers >> (bc - 12) : verinfo >> bc))
	{
	  SETQRBIT (5 - x, 2 - y + WD - 11);
	  SETQRBIT (2 - y + WD - 11, 5 - x);
	}
      else
	{
	  setmask (5 - x, 2 - y + WD - 11);
	  setmask (2 - y + WD - 11, 5 - x);
	}
}

void
initframe ()
{
  unsigned x, y;

  framebase = calloc_beebs (WDB * WD, 1);
  framask = calloc_beebs (((WD * (WD + 1) / 2) + 7) / 8, 1);
  rlens = malloc_beebs (WD + 1);
  // finders
  putfind ();
  // alignment blocks
  doaligns ();
  // single black
  SETQRBIT (8, WD - 8);
  // timing gap - masks only
  for (y = 0; y < 7; y++)
    {
      setmask (7, y);
      setmask (WD - 8, y);
      setmask (7, y + WD - 7);
    }
  for (x = 0; x < 8; x++)
    {
      setmask (x, 7);
      setmask (x + WD - 8, 7);
      setmask (x, WD - 8);
    }
  // reserve mask-format area
  for (x = 0; x < 9; x++)
    setmask (x, 8);
  for (x = 0; x < 8; x++)
    {
      setmask (x + WD - 8, 8);
      setmask (8, x);
    }
  for (y = 0; y < 7; y++)
    setmask (8, y + WD - 7);
  // timing
  for (x = 0; x < (unsigned) WD - 14; x++)
    if (x & 1)
      {
	setmask (8 + x, 6);
	setmask (6, 8 + x);
      }
    else
      {
	SETQRBIT (8 + x, 6);
	SETQRBIT (6, 8 + x);
      }

  // version block
  putvpat ();
  for (y = 0; y < WD; y++)
    for (x = 0; x <= y; x++)
      if (QRBIT (x, y))
	setmask (x, y);
}

void
freeframe ()
{
  free_beebs (framebase);
  free_beebs (framask);
  free_beebs (rlens);
}

unsigned char *strinbuf;
unsigned char *qrframe;
unsigned char ECCLEVEL;
unsigned char neccblk1;
unsigned char neccblk2;
unsigned char datablkw;
unsigned char eccblkwid;

#ifndef __AVR__
#define PROGMEM
#define memcpy_P memcpy
#define __LPM(x) *x
#endif

#include "ecctable.h"

unsigned
initecc (unsigned char ecc, unsigned char vers)
{
  VERSION = vers;
  WD = 17 + 4 * vers;
  WDB = (WD + 7) / 8;

  unsigned fsz = WD * WDB;
  if (fsz < 768)		// for ECC math buffers
    fsz = 768;
  qrframe = malloc_beebs (fsz);

  ECCLEVEL = ecc;
  unsigned eccindex = (ecc - 1) * 4 + (vers - 1) * 16;

  neccblk1 = eccblocks[eccindex++];
  neccblk2 = eccblocks[eccindex++];
  datablkw = eccblocks[eccindex++];
  eccblkwid = eccblocks[eccindex++];

  if (fsz <
      (unsigned) (datablkw + (datablkw + eccblkwid) * (neccblk1 + neccblk2) +
		  neccblk2))
    fsz =
      datablkw + (datablkw + eccblkwid) * (neccblk1 + neccblk2) + neccblk2;
  strinbuf = malloc_beebs (fsz);
  return datablkw * (neccblk1 + neccblk2) + neccblk2 - 3;	//-2 if vers <= 9!
}

unsigned
initeccsize (unsigned char ecc, unsigned size)
{
  unsigned eccindex;
  unsigned char vers;
  for (vers = 1; vers < 40; vers++)
    {
      eccindex = (ecc - 1) * 4 + (vers - 1) * 16;
      neccblk1 = eccblocks[eccindex++];
      neccblk2 = eccblocks[eccindex++];
      datablkw = eccblocks[eccindex++];
      if (size < (unsigned) (datablkw * (neccblk1 + neccblk2) + neccblk2 - 3))
	break;
    }
  return initecc (ecc, vers);
}

void
freeecc ()
{
  free_beebs (qrframe);
  free_beebs (strinbuf);
}


/*
   Local Variables:
   mode: C
   c-file-style: "gnu"
   End:
*/
