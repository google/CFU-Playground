/* BEEBS slre benchmark

   Copyright (c) 2004-2013 Sergey Lyubka <valenok@gmail.com>
   Copyright (c) 2013 Cesanta Software Limited.  All rights reserved
   Copyright (C) 2014 Embecosm Limited and University of Bristol

   This version, copyright (C) 2014-2019 Embecosm Limited and University of
   Bristol

   Contributor James Pallister <james.pallister@bristol.ac.uk>
   Contributor Jeremy Bennett <jeremy.bennett@embecosm.com>

   This file is part of Embench and was formerly part of the Bristol/Embecosm
   Embedded Benchmark Suite.

   SPDX-License-Identifier: GPL-3.0-or-later */

#ifndef SLRE_HEADER_DEFINED
#define SLRE_HEADER_DEFINED

#ifdef __cplusplus
extern "C"
{
#endif

  struct slre_cap
  {
    const char *ptr;
    int len;
  };

  int slre_match (const char *regexp, const char *buf, int buf_len,
		  struct slre_cap *caps, int num_caps);

/* slre_match() failure codes */
#define SLRE_NO_MATCH               -1
#define SLRE_UNEXPECTED_QUANTIFIER  -2
#define SLRE_UNBALANCED_BRACKETS    -3
#define SLRE_INTERNAL_ERROR         -4
#define SLRE_INVALID_CHARACTER_SET  -5
#define SLRE_INVALID_METACHARACTER  -6
#define SLRE_CAPS_ARRAY_TOO_SMALL   -7
#define SLRE_TOO_MANY_BRANCHES      -8
#define SLRE_TOO_MANY_BRACKETS      -9

#ifdef __cplusplus
}
#endif

#endif				/* SLRE_HEADER_DEFINED */


/*
   Local Variables:
   mode: C
   c-file-style: "gnu"
   End:
*/
