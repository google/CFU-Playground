/* BEEBS st benchmark

   This version, copyright (C) 2014-2019 Embecosm Limited and University of
   Bristol

   Contributor James Pallister <james.pallister@bristol.ac.uk>
   Contributor Jeremy Bennett <jeremy.bennett@embecosm.com>

   This file is part of Embench and was formerly part of the Bristol/Embecosm
   Embedded Benchmark Suite.

   SPDX-License-Identifier: GPL-3.0-or-later */

/* stats.c */

/* 2012/09/28, Jan Gustafsson <jan.gustafsson@mdh.se>
 * Changes:
 *  - time is only enabled if the POUT flag is set
 *  - st.c:30:1:  main () warning: type specifier missing, defaults to 'int':
 *    fixed
 */


/* 2011/10/18, Benedikt Huber <benedikt@vmars.tuwien.ac.at>
 * Changes:
 *  - Measurement and Printing the Results is only enabled if the POUT flag is
 *    set
 *  - Added Prototypes for InitSeed and RandomInteger
 *  - Changed return type of InitSeed from 'missing (default int)' to 'void'
 */

#include <math.h>
#include "third_party/embench_iot_v1/support/support.h"

/* This scale factor will be changed to equalise the runtime of the
   benchmarks. */
#define LOCAL_SCALE_FACTOR 13

#define MAX 100

void InitSeed_st (void);
int RandomInteger_st ();
void Initialize (double[]);
void Calc_Sum_Mean (double[], double *, double *);
void Calc_Var_Stddev (double[], double, double *, double *);
void Calc_LinCorrCoef (double[], double[], double, double);


/* Statistics Program:
 * This program computes for two arrays of numbers the sum, the
 * mean, the variance, and standard deviation.  It then determines the
 * correlation coefficient between the two arrays.
 */

int Seed_st;
double ArrayA_st[MAX], ArrayB_st[MAX];
double SumA, SumB;
double Coef;


void
initialise_benchmark_st (void)
{
}


static int benchmark_body_st (int  rpt);

void
warm_caches_st (int  heat)
{
  benchmark_body_st (heat);

  return;
}


int
benchmark_st (void)
{
  return benchmark_body_st (LOCAL_SCALE_FACTOR * CPU_MHZ);
}


static int __attribute__ ((noinline))
benchmark_body_st (int rpt)
{
  int i;

  for (i = 0; i < rpt; i++)
    {
      double MeanA, MeanB, VarA, VarB, StddevA, StddevB /*, Coef */ ;

      InitSeed_st ();

      Initialize (ArrayA_st);
      Calc_Sum_Mean (ArrayA_st, &SumA, &MeanA);
      Calc_Var_Stddev (ArrayA_st, MeanA, &VarA, &StddevA);

      Initialize (ArrayB_st);
      Calc_Sum_Mean (ArrayB_st, &SumB, &MeanB);
      Calc_Var_Stddev (ArrayB_st, MeanB, &VarB, &StddevB);

      /* Coef will have to be used globally in Calc_LinCorrCoef since it would
         be beyond the 6 registers used for passing parameters
       */
      Calc_LinCorrCoef (ArrayA_st, ArrayB_st, MeanA, MeanB /*, &Coef */ );
    }

  return 0;
}


void
InitSeed_st ()
/*
 * Initializes the seed used in the random number generator.
 */
{
  Seed_st = 0;
}


void
Calc_Sum_Mean (double Array[], double *Sum, double *Mean)
{
  int i;

  *Sum = 0;
  for (i = 0; i < MAX; i++)
    *Sum += Array[i];
  *Mean = *Sum / MAX;
}


double
Square (double x)
{
  return x * x;
}


void
Calc_Var_Stddev (double Array[], double Mean, double *Var, double *Stddev)
{
  int i;
  double diffs;

  diffs = 0.0;
  for (i = 0; i < MAX; i++)
    diffs += Square (Array[i] - Mean);
  *Var = diffs / MAX;
  *Stddev = sqrt (*Var);
}


void
Calc_LinCorrCoef (double local_ArrayA_st[], double local_ArrayB_st[], double MeanA,
		  double MeanB /*, Coef */ )
{
  int i;
  double numerator, Aterm, Bterm;

  numerator = 0.0;
  Aterm = Bterm = 0.0;
  for (i = 0; i < MAX; i++)
    {
      numerator += (local_ArrayA_st[i] - MeanA) * (local_ArrayB_st[i] - MeanB);
      Aterm += Square (local_ArrayA_st[i] - MeanA);
      Bterm += Square (local_ArrayB_st[i] - MeanB);
    }

  /* Coef used globally */
  Coef = numerator / (sqrt (Aterm) * sqrt (Bterm));
}



void
Initialize (double Array[])
/*
 * Intializes the given array with random integers.
 */
{
  register int i;

  for (i = 0; i < MAX; i++)
    Array[i] = i + RandomInteger_st () / 8095.0;
}


int
RandomInteger_st ()
/*
 * Generates random integers between 0 and 8095
 */
{
  Seed_st = ((Seed_st * 133) + 81) % 8095;
  return (Seed_st);
}

int
verify_benchmark_st (int unused)
{
  double expSumA = 4999.00247066090196;
  double expSumB = 4996.84311303273534;
  double expCoef = 0.999900054853619324;

  return double_eq_beebs(expSumA, SumA)
    && double_eq_beebs(expSumB, SumB)
    && double_eq_beebs(expCoef, Coef);
}


/*
   Local Variables:
   mode: C
   c-file-style: "gnu"
   End:
*/
