/* BEEBS nbody benchmark

   This version, copyright (C) 2014-2019 Embecosm Limited and University of
   Bristol

   Contributor Jeremy Bennett <jeremy.bennett@embecosm.com>

   This file is part of Embench and was formerly part of the Bristol/Embecosm
   Embedded Benchmark Suite.

   SPDX-License-Identifier: GPL-3.0-or-later

   The original source code for this benchmark can be found here:

     http://benchmarksgame.alioth.debian.org/

   and was released under the following licence, disclaimers, and
   copyright:

   Revised BSD license

   This is a specific instance of the Open Source Initiative (OSI) BSD
   license template http://www.opensource.org/licenses/bsd-license.php

   Copyright 2004-2009 Brent Fulgham
   All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions
   are met:

   Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.

   Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the
   distribution.

   Neither the name of "The Computer Language Benchmarks Game" nor the
   name of "The Computer Language Shootout Benchmarks" nor the names
   of its contributors may be used to endorse or promote products
   derived from this software without specific prior written
   permission.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
   FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
   COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
   INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
   HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
   STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
   ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
   OF THE POSSIBILITY OF SUCH DAMAGE.  */

#include <math.h>
#include <stdlib.h>

#include "third_party/embench_iot_v1/support/support.h"

#define LOCAL_SCALE_FACTOR 1

#define PI 3.141592653589793
#define SOLAR_MASS ( 4 * PI * PI )
#define DAYS_PER_YEAR 365.24

struct body
{
  double x[3], fill, v[3], mass;
};

static struct body solar_bodies[] = {
  /* sun */
  {
   .x = {0., 0., 0.},
   .v = {0., 0., 0.},
   .mass = SOLAR_MASS},
  /* jupiter */
  {
   .x = {4.84143144246472090e+00,
	 -1.16032004402742839e+00,
	 -1.03622044471123109e-01},
   .v = {1.66007664274403694e-03 * DAYS_PER_YEAR,
	 7.69901118419740425e-03 * DAYS_PER_YEAR,
	 -6.90460016972063023e-05 * DAYS_PER_YEAR},
   .mass = 9.54791938424326609e-04 * SOLAR_MASS},
  /* saturn */
  {
   .x = {8.34336671824457987e+00,
	 4.12479856412430479e+00,
	 -4.03523417114321381e-01},
   .v = {-2.76742510726862411e-03 * DAYS_PER_YEAR,
	 4.99852801234917238e-03 * DAYS_PER_YEAR,
	 2.30417297573763929e-05 * DAYS_PER_YEAR},
   .mass = 2.85885980666130812e-04 * SOLAR_MASS},
  /* uranus */
  {
   .x = {1.28943695621391310e+01,
	 -1.51111514016986312e+01,
	 -2.23307578892655734e-01},
   .v = {2.96460137564761618e-03 * DAYS_PER_YEAR,
	 2.37847173959480950e-03 * DAYS_PER_YEAR,
	 -2.96589568540237556e-05 * DAYS_PER_YEAR},
   .mass = 4.36624404335156298e-05 * SOLAR_MASS},
  /* neptune */
  {
   .x = {1.53796971148509165e+01,
	 -2.59193146099879641e+01,
	 1.79258772950371181e-01},
   .v = {2.68067772490389322e-03 * DAYS_PER_YEAR,
	 1.62824170038242295e-03 * DAYS_PER_YEAR,
	 -9.51592254519715870e-05 * DAYS_PER_YEAR},
   .mass = 5.15138902046611451e-05 * SOLAR_MASS}
};

static const int BODIES_SIZE =
  sizeof (solar_bodies) / sizeof (solar_bodies[0]);

void
offset_momentum (struct body *bodies, unsigned int nbodies)
{
  unsigned int i, k;
  for (i = 0; i < nbodies; ++i)
    for (k = 0; k < 3; ++k)
      bodies[0].v[k] -= bodies[i].v[k] * bodies[i].mass / SOLAR_MASS;
}


double
bodies_energy (struct body *bodies, unsigned int nbodies)
{
  double dx[3], distance, e = 0.0;
  unsigned int i, j, k;

  for (i = 0; i < nbodies; ++i)
    {
      e += bodies[i].mass * (bodies[i].v[0] * bodies[i].v[0]
			     + bodies[i].v[1] * bodies[i].v[1]
			     + bodies[i].v[2] * bodies[i].v[2]) / 2.;

      for (j = i + 1; j < nbodies; ++j)
	{
	  for (k = 0; k < 3; ++k)
	    dx[k] = bodies[i].x[k] - bodies[j].x[k];

	  distance = sqrt (dx[0] * dx[0] + dx[1] * dx[1] + dx[2] * dx[2]);
	  e -= (bodies[i].mass * bodies[j].mass) / distance;
	}
    }
  return e;
}

void
initialise_benchmark_nbody (void)
{
}



static int benchmark_body_nbody (int  rpt);

void
warm_caches_nbody (int  heat)
{
  benchmark_body_nbody (heat);

  return;
}


int
benchmark_nbody (void)
{
  return benchmark_body_nbody (LOCAL_SCALE_FACTOR * CPU_MHZ);
}


static int __attribute__ ((noinline))
benchmark_body_nbody (int rpt)
{
  int j;
  double tot_e = 0.0;

  for (j = 0; j < rpt; j++)
    {
      int i;
      offset_momentum (solar_bodies, BODIES_SIZE);
      /*printf("%.9f\n", bodies_energy(solar_bodies, BODIES_SIZE)); */
      tot_e = 0.0;
      for (i = 0; i < 100; ++i)
	tot_e += bodies_energy (solar_bodies, BODIES_SIZE);
      /*printf("%.9f\n", bodies_energy(solar_bodies, BODIES_SIZE)); */
    }
  /* Result is known good value for total energy. */
  return double_eq_beebs(tot_e, -16.907516382852478);
}


int
verify_benchmark_nbody (int tot_e_ok)
{
  int i, j;
  /* print expected values */
  // printf("static struct body solar_bodies[] = {\n");
  // for (i=0; i<BODIES_SIZE; i++) {
  //    printf("  {\n");
  //    printf("    .x = { %.30g, %.30g, %.30g },\n", solar_bodies[i].x[0],  solar_bodies[i].x[1],  solar_bodies[i].x[2]);
  //    printf("    .v = { %.30g, %.30g, %.30g },\n", solar_bodies[i].v[0],  solar_bodies[i].v[1],  solar_bodies[i].v[2]);
  //    printf("    .mass = %.30g\n", solar_bodies[i].mass);
  //    printf("  }");
  //    if (i<BODIES_SIZE-1) printf(",");
  //    printf("\n");
  // }
  // printf("};\n");
  static struct body expected[] = {
    {
     .x = {0, 0, 0},
     .v =
     {-0.000387663407198742665776131088862,
      -0.0032753590371765706722173572274,
      2.39357340800030020670947916717e-05},
     .mass = 39.4784176043574319692197605036},
    {
     .x =
     {4.84143144246472090230781759601, -1.16032004402742838777840006514,
      -0.103622044471123109232735259866},
     .v =
     {0.606326392995832019749968821998, 2.81198684491626016423992950877,
      -0.0252183616598876288172892401462},
     .mass = 0.0376936748703894930478952574049},
    {
     .x =
     {8.34336671824457987156620220048, 4.1247985641243047894022311084,
      -0.403523417114321381049535375496},
     .v =
     {-1.01077434617879236000703713216, 1.82566237123041186229954746523,
      0.00841576137658415351916474378413},
     .mass = 0.0112863261319687668143840753032},
    {
     .x =
     {12.8943695621391309913406075793, -15.1111514016986312469725817209,
      -0.223307578892655733682204299839},
     .v =
     {1.08279100644153536414648897335, 0.868713018169608219842814378353,
      -0.0108326374013636358983880825235},
     .mass = 0.0017237240570597111687795033319},
    {
     .x =
     {15.3796971148509165061568637611, -25.9193146099879641042207367718,
      0.179258772950371181309492385481},
     .v =
     {0.979090732243897976516677772452, 0.594698998647676169149178804219,
      -0.0347559555040781037460462243871},
     .mass = 0.00203368686992463042206846779436}
  };

  /* Check we have the correct total energy and we have set up the
     solar_bodies array correctly. */

  if (tot_e_ok)
    for (i = 0; i < BODIES_SIZE; i++)
      {
	for (j = 0; j < 3; j++)
	  {
	    if (double_neq_beebs(solar_bodies[i].x[j], expected[i].x[j]))
	      return 0;
	    if (double_neq_beebs(solar_bodies[i].v[j], expected[i].v[j]))
	      return 0;
	  }
	if (double_neq_beebs(solar_bodies[i].mass, expected[i].mass))
	  return 0;
      }
  else
    return 0;

  return 1;
}


/*
   Local Variables:
   mode: C
   c-file-style: "gnu"
   End:
*/
