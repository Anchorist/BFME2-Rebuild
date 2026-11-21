// cl: /O2 /G6 /Oi
// psdk
#include <windows.h>
#include <math.h>
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G0002FB30 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x0002FB30 size=38 name=?BFME2WideToUtf8@@YAHPBGHPADH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
int BFME2WideToUtf8(const unsigned short *src, int srcLen, char *dst, int dstLen)
{
	return WideCharToMultiByte(CP_UTF8, 0, (LPCWSTR)src, srcLen, dst, dstLen, 0, 0);
}
// FUNCTION: BFME2 0x0002FB60 size=34 name=?BFME2Utf8ToWide@@YAHPBDHPAGH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
int BFME2Utf8ToWide(const char *src, int srcLen, unsigned short *dst, int dstLen)
{
	return MultiByteToWideChar(CP_UTF8, 0, src, srcLen, (LPWSTR)dst, dstLen);
}
// FUNCTION: BFME2 0x0002FB90 size=10 name=?ACos@@YAMM@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0002FBA0 size=9 name=?Tan@@YAMM@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
float Tan(float x)
{
	return tanf(x);
}
// FUNCTION: BFME2 0x0002FBD0 size=54 name=?rva0002FBD0@@YAPAXII@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0002FC10 size=29 name=?rva0002FC10@@YAXPAX@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0002FC30 size=35 name=?rva0002FC30@@YAXPAXH@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0002FC60 size=19 name=?rva0002FC60@@YAPAXI@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
