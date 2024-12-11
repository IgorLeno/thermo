
/*******************************************
****   HyperDrive 2.0 - OpenCL program  ****
**** (c) 2010-2023, Alessandro Pedretti ****
*******************************************/


/**** Local prototypes ****/

float CosBondAngle(float4 a, float4 b, float4 c);


/**** HbAcc surface ****/

__kernel void SrfHbAcc(__global float4 *IntSrf, __global float *IntSrfVal,
                       const unsigned int TotSrf,
                       __global float4 *IntAtm, __global float *IntEps,
                       __global float *IntRmin, const unsigned int TotAtm,
                       const float HBDA, const int REXP, const int AEXP)
{
  uint     Tid = get_global_id(0);
  if (Tid >= TotSrf) return;

  float    Rmin;
  float    Ene = 0.0f;
  float4   Srf = IntSrf[Tid];

  for(uint k = 0; k < TotAtm; ++k) {
    Rmin  = IntRmin[k] / (fast_distance(Srf, IntAtm[k]) + HBDA);
    Ene  += (- IntEps[k] * (pown(Rmin, REXP) - 2.0f * pown(Rmin, AEXP)));
  } /* End of for (k) */

  IntSrfVal[Tid] = Ene;
}


/**** Deep surface ****/

__kernel void SrfDeep(__global float4 *IntSrf, __global float *IntSrfVal,
                       const unsigned int TotSrf, const float4 GeoCent)
{
  uint     Tid = get_global_id(0);
  if (Tid >= TotSrf) return;

  IntSrfVal[Tid] = fast_distance(IntSrf[Tid], GeoCent);
}


/**** HbDon surface ****/

__kernel void SrfHbDon(__global float4 *IntSrf, __global float *IntSrfVal,
                       const unsigned int TotSrf,
                       __global float4 *IntDon,
                       __global float *IntDon2Eps, __global float *IntDon2Rmin, const unsigned int TotAtm,
                       const float HBDA, const int HAEX, const int AAEX,
                       const int REXP, const int AEXP)
{
  uint     Tid = get_global_id(0);
  if (Tid >= TotSrf) return;

  float    Rmin;
  float    Ene = 0.0f;
  float4   Srf = IntSrf[Tid];

  for(uint k = 0; k < TotAtm; ++k) {
    Rmin = IntDon2Rmin[k] / (fast_distance(Srf, IntDon[0]) + HBDA);
    Ene += (- IntDon2Eps[k] * (pown(Rmin, REXP) - 2.0f * pown(Rmin, AEXP))) *
            pown(CosBondAngle(IntDon[0], IntDon[1], IntDon[2]), HAEX) *
            pown(CosBondAngle(Srf, IntDon[0], IntDon[1]), AAEX);
    IntDon += 3;
  }

  IntSrfVal[Tid] = Ene;
}


/**** MEP surface ****/

__kernel void SrfMep(__global float4 *IntSrf, __global float *IntSrfVal,
                     const unsigned int TotSrf,
                     __global float4 *IntAtm, __global float *IntAtmCharge,
                     const unsigned int TotAtm)
{
  uint     Tid = get_global_id(0);
  if (Tid >= TotSrf) return;

  float    Val = 0.0f;
  float4   Srf = IntSrf[Tid];

  for(uint k = 0; k < TotAtm; ++k)
    Val += IntAtmCharge[k] / fast_distance(Srf, IntAtm[k]);

  IntSrfVal[Tid] = Val;
}


/**** MLP surface ****/

__kernel void SrfMlp(__global float4 *IntSrf, __global float *IntSrfVal,
                     const unsigned int TotSrf,
                     __global float4 *IntAtm, __global float *Contrib,
                     const unsigned int TotAtm)
{
  uint     Tid = get_global_id(0);
  if (Tid >= TotSrf) return;

  float    Val = 0.0f;
  float4   Srf = IntSrf[Tid];

  for(uint k = 0; k < TotAtm; ++k)
    Val += (1.01326667f / (1.0f + exp(1.33f * (fast_distance(Srf, IntAtm[k]) - 3.25f)))) * Contrib[k];

  IntSrfVal[Tid] = Val;
}


/**** Smoothed PSA surface ****/

__kernel void SrfPsa(__global float4 *IntSrf, __global float *IntSrfVal,
                     const unsigned int TotSrf,
                     __global float4 *IntAtm, __global float *IntAtmVal,
                     const unsigned int TotAtm)
{
  uint     Tid = get_global_id(0);
  if (Tid >= TotSrf) return;

  float    Val = 0.0f;
  float4   Srf = IntSrf[Tid];

  for(uint k = 0; k < TotAtm; ++k)
    Val += IntAtmVal[k] / fast_distance(Srf, IntAtm[k]);

  IntSrfVal[Tid] = Val;
}


/**** Measures the cosine of bond angle ****/

float CosBondAngle(float4 a, float4 b, float4 c)
{
  float     Val = fast_distance(a, b) * fast_distance(b, c);

  if (Val == 0.0f) return 1.0f;

  a -= b;
  c -= b;
  Val = dot(a, c) / Val;

  return (Val > 1.0f ? 1.0f : Val < -1.0f ? -1.0f : Val);
}
