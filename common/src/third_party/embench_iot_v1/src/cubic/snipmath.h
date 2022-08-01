/* BEEBS cubic benchmark

   This version, copyright (C) 2013-2019 Embecosm Limited and University of
   Bristol

   Contributor: James Pallister <james.pallister@bristol.ac.uk>
   Contributor Jeremy Bennett <jeremy.bennett@embecosm.com>

   This file is part of Embench and was formerly part of the Bristol/Embecosm
   Embedded Benchmark Suite.

   SPDX-License-Identifier: GPL-3.0-or-later

   The original code is from http://www.snippets.org/. */

/* +++Date last modified: 05-Jul-1997 */

/*
 **  SNIPMATH.H - Header file for SNIPPETS math functions and macros
 */

#ifndef SNIPMATH__H
#define SNIPMATH__H

#include <math.h>

#include "pi.h"
#include "sniptype.h"

/*
 **  Callable library functions begin here
 */

void SolveCubic (double a, double b, double c,	/* Cubic.C        */
		 double d, int *solutions, double *x);


/*
 **  File: ISQRT.C
 */

struct int_sqrt
{
  unsigned sqrt, frac;
};

#endif /* SNIPMATH__H */

/* vim: set ts=3 sw=3 et: */


/*
   Local Variables:
   mode: C
   c-file-style: "gnu"
   End:
*/
