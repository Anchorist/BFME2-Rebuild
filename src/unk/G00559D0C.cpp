// cl: /O1
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G00559D0C name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include <stdlib.h>
#include <string.h>
#include "Common/GameType.h"
// FUNCTION: BFME2 0x00559D0C size=148 name=?rva00559D0C@Rva00559D0CRankWeights@@QBEHPBVRva00553E47StatsCore@@@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00559DA0 size=168 name=?rva00559DA0@Rva00559D0CRankWeights@@QBEHPBVRva00553E47StatsCore@@H@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00559E48 size=148 name=?rva00559E48@Rva00559D0CRankWeights@@QBEHPBVRva00553E47StatsCore@@@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00559EDC size=34 name=?Rva00559EDCCompare@@YAHPAH0@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
Int Rva00559EDCCompare(Int *a, Int *b)
{
	Int diff = 0;
	for (Int i = 0; i < 10; ++i)
	{
		if (a[i] != b[i])
			++diff;
	}
	return diff;
}
// FUNCTION: BFME2 0x00559EFE size=19 name=?copyRecord@@YAXPAXPBX@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void copyRecord(void *dst, const void *src)
{
	memcpy(dst, src, 40);
}
// FUNCTION: BFME2 0x00559F11 size=55 name=?Rva00559F11Parse@@YAXPBDPAH@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
void Rva00559F11Parse(const char *str, Int *out)
{
	for (Int i = 0; i < 10; ++i)
	{
		out[i] = atoi(str);
		while (*str && *str != ' ')
			++str;
		if (*str)
			++str;
	}
}
// FUNCTION: BFME2 0x00559F48 size=27 name=?Rva00559F48Get@@YAPBQBURuleCombo@@H@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00559F63 size=27 name=?Rva00559F63Get@@YAPBQBURuleCheck@@H@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00559F7E size=23 name=?Rva00559F7EGet@@YAHH@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
Int Rva00559F7EGet(Int mode)
{
	switch (mode)
	{
		case 0: return 2;
		case 1: return 4;
		default: return 0;
	}
}
// FUNCTION: BFME2 0x00559F95 size=23 name=?Rva00559F95Get@@YAHH@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
Int Rva00559F95Get(Int mode)
{
	switch (mode)
	{
		case 0: return 3;
		case 1: return 2;
		default: return 0;
	}
}
