// cl: /O1 /EHs /EHc-
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G0055A087 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/AsciiString.h"

// FUNCTION: BFME2 0x0055A087 size=86 name=?Rva0055A087Format@@YAXPAHPAVAsciiString@@@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
void Rva0055A087Format(Int *rules, AsciiString *out)
{
	AsciiString tmp;
	for (Int i = 0; i < 10; ++i)
	{
		tmp.format("%d ", rules[i]);
		out->concat(tmp);
	}
}
