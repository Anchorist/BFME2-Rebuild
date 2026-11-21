// mpmath.h: WWLib's multiple-precision integer primitives (the XMP_* family).
// Target facts (retail game.dat): plain C functions in the 0x0061BD70 object, cdecl, taking
// little-endian arrays of 32-bit words and the word count (the "precision"). XMP_Init
// 0x0061BD70 clears the array and stores the value in word 0; XMP_Count_Bits 0x0061BD90
// returns the number of significant bits; XMP_DER_Encode 0x0061C580 and XMP_DER_Decode
// 0x0061C5E0 convert between a word array and a DER byte string.
#pragma once
#ifndef BFME2_MPMATH_H
#define BFME2_MPMATH_H

typedef unsigned int digit;
class Straw;

extern "C" {
void XMP_Init(unsigned int *number, unsigned int value, int precision);		// 0x0061BD70
unsigned int XMP_Count_Bits(const unsigned int *number, int precision);			// 0x0061BD90
int XMP_DER_Encode(const unsigned int *number, unsigned char *output, int precision);	// 0x0061C580
void XMP_DER_Decode(unsigned int *number, const unsigned char *input, int precision);	// 0x0061C5E0
int XMP_Exponent_Mod(unsigned int *expout, const unsigned int *expin, const unsigned int *exponent_ptr, const unsigned int *modulus, int precision);	// 0x0061D4C0
int XMP_Fetch_Prime_Size(void);
int XMP_Significance(const digit *r, int precision);
void XMP_Inc(digit *r, int precision);
void XMP_Dec(digit *r, int precision);
void XMP_Neg(digit *r, int precision);
void XMP_Abs(digit *r, int precision);
void XMP_Shift_Right_Bits(digit *r1, int bits, int precision);
void XMP_Shift_Left_Bits(digit *r1, int bits, int precision);
bool XMP_Rotate_Left(digit *r1, bool carry, int precision);
void XMP_Not(digit *digit_ptr, int precision);
int XMP_Prepare_Modulus(const digit *n_modulus, int precision);
int XMP_Count_Bytes(const digit *r, int precision);
void XMP_Move(digit *dest, digit const *source, int precision);
int XMP_Compare(const digit *r1, const digit *r2, int precision);
bool XMP_Add(digit *result, const digit *r1, const digit *r2, bool carry, int precision);
bool XMP_Add_Int(digit *result, const digit *r1, digit r2, bool carry, int precision);
bool XMP_Test_Eq_Int(digit const *r, int i, int p);
bool XMP_Sub(digit *result, const digit *r1, const digit *r2, bool borrow, int precision);
bool XMP_Sub_Int(digit *result, const digit *r1, unsigned short r2, bool borrow, int precision);
int XMP_Unsigned_Mult(digit *prod, const digit *multiplicand, const digit *multiplier, int precision);
int XMP_Unsigned_Mult_Int(digit *prod, const digit *multiplicand, short multiplier, int precision);
int XMP_Signed_Mult_Int(digit *prod, const digit *multiplicand, signed short multiplier, int precision);
int XMP_Signed_Mult(digit *prod, const digit *multiplicand, const digit *multiplier, int precision);
unsigned short XMP_Unsigned_Div_Int(digit *quotient, digit const *dividend, unsigned short divisor, int precision);
int XMP_Unsigned_Div(digit *remainder, digit *quotient, digit const *dividend, digit const *divisor, int precision);
void XMP_Signed_Div(digit *remainder, digit *quotient, digit const *dividend, digit const *divisor, int precision);
int XMP_Reciprocal(digit *quotient, const digit *divisor, int precision);
void XMP_Decode_ASCII(char const *str, digit *mpn, int precision);
void XMP_Double_Mul(digit *prod, const digit *multiplicand, const digit *multiplier, int precision);
int XMP_Mod_Mult(digit *prod, const digit *multiplicand, const digit *multiplier, int precision);
void XMP_Mod_Mult_Clear(int precision);
bool XMP_Is_Small_Prime(const digit *candidate, int precision);
bool XMP_Small_Divisors_Test(const digit *candidate, int precision);
bool XMP_Fermat_Test(const digit *candidate_prime, unsigned rounds, int precision);
void XMP_Inverse_A_Mod_B(digit *result, digit const *number, digit const *modulus, int precision);
void XMP_Signed_Decode(digit *result, const unsigned char *from, int frombytes, int precision);
void XMP_Unsigned_Decode(digit *result, const unsigned char *from, int frombytes, int precision);
unsigned XMP_Encode(unsigned char *to, digit const *from, int precision);
unsigned XMP_Encode_Bounded(unsigned char *to, unsigned tobytes, digit const *from, int precision);
void XMP_Randomize(digit *result, Straw &rng, int nbits, int precision);
void XMP_Randomize_Bounded(digit *result, Straw &rng, digit const *min, digit const *max, int precision);
bool XMP_Is_Prime(digit const *prime, int precision);
bool XMP_Rabin_Miller_Test(Straw &rng, digit const *w, int rounds, int precision);
int XMP_DER_Length_Encode(unsigned long length, unsigned char *output);
}

#endif
