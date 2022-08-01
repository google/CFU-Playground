/* BEEBS qrduino benchmark

   This version, copyright (C) 2014-2019 Embecosm Limited and University of
   Bristol

   Contributor James Pallister <james.pallister@bristol.ac.uk>
   Contributor Jeremy Bennett <jeremy.bennett@embecosm.com>

   This file is part of Embench and was formerly part of the Bristol/Embecosm
   Embedded Benchmark Suite.

   SPDX-License-Identifier: GPL-3.0-or-later

   Original code from: https://github.com/tz1/qrduino */

#define QRBIT(x,y) ( ( qrframe[((x)>>3) + (y) * WDB] >> (7-((x) & 7 ))) & 1 )
#define SETQRBIT(x,y) qrframe[((x)>>3) + (y) * WDB] |= 0x80 >> ((x) & 7)
#define TOGQRBIT(x,y) qrframe[((x)>>3) + (y) * WDB] ^= 0x80 >> ((x) & 7)


/*
   Local Variables:
   mode: C
   c-file-style: "gnu"
   End:
*/
