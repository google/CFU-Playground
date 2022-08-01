/* BEEBS cubic benchmark

   Contributor: James Pallister <james.pallister@bristol.ac.uk>

   This file is part of Embench and was formerly part of the Bristol/Embecosm
   Embedded Benchmark Suite.

   SPDX-License-Identifier: GPL-3.0-or-later */

#include <string.h>
#include "third_party/embench_iot_v1/support/support.h"
#include "snipmath.h"

/* This scale factor will be changed to equalise the runtime of the
   benchmarks. */
#define LOCAL_SCALE_FACTOR 10




static int soln_cnt0;
static int soln_cnt1;
static double res0[3];
static double res1;


int
verify_benchmark_cubic (int res __attribute ((unused)) )
{
  static const double exp_res0[3] = {2.0, 6.0, 2.5};
  const double exp_res1 = 2.5;
  return (3 == soln_cnt0)
    && double_eq_beebs(exp_res0[0], res0[0])
    && double_eq_beebs(exp_res0[1], res0[1])
    && double_eq_beebs(exp_res0[2], res0[2])
    && (1 == soln_cnt1)
    && double_eq_beebs(exp_res1, res1);
}


void
initialise_benchmark_cubic (void)
{
}


static int benchmark_body_cubic (int  rpt);

void
warm_caches_cubic (int  heat)
{
  benchmark_body_cubic (heat);

  return;
}


int
benchmark_cubic (void)
{
  return benchmark_body_cubic (LOCAL_SCALE_FACTOR * CPU_MHZ);
}


static int
benchmark_body_cubic (int rpt)
{
  int  i;

  for (i = 0; i < rpt; i++)
    {
      double  a1 = 1.0, b1 = -10.5, c1 = 32.0, d1 = -30.0;
      double  a2 = 1.0, b2 = -4.5, c2 = 17.0, d2 = -30.0;
      double  a3 = 1.0, b3 = -3.5, c3 = 22.0, d3 = -31.0;
      double  a4 = 1.0, b4 = -13.7, c4 = 1.0, d4 = -35.0;
      int     solutions;

      double output[48] = {0};
      double *output_pos = &(output[0]);

      /* solve some cubic functions */
      /* should get 3 solutions: 2, 6 & 2.5   */
      SolveCubic(a1, b1, c1, d1, &solutions, output);
      soln_cnt0 = solutions;
      memcpy(res0,output,3*sizeof(res0[0]));
      /* should get 1 solution: 2.5           */
      SolveCubic(a2, b2, c2, d2, &solutions, output);
      soln_cnt1 = solutions;
      res1 = output[0];
      SolveCubic(a3, b3, c3, d3, &solutions, output);
      SolveCubic(a4, b4, c4, d4, &solutions, output);
      /* Now solve some random equations */
      for(a1=1;a1<3;a1++) {
	for(b1=10;b1>8;b1--) {
	  for(c1=5;c1<6;c1+=0.5) {
            for(d1=-1;d1>-3;d1--) {
	      SolveCubic(a1, b1, c1, d1, &solutions, output_pos);
            }
	  }
	}
      }
    }

   return 0;
}


/* vim: set ts=3 sw=3 et: */
