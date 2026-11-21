// cl: /O1 /D_BFME_RETAIL_TREE_INSERT_LAYOUT /D_STLP_USE_MALLOC /D_STLP_USE_STATIC_LIB /D_STLP_BFME_COPY_TRIVIAL_EXTERN /D_STLP_NO_EXCEPTIONS
// stlport46
#include "GameClient/MapCache.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G00300489 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x00300489 size=28 name=?getMapDir@MapCache@@UBE?AVAsciiString@@XZ evidence=X:proven (caller-this) tier=B hypothesis:mm1-gap-unit
AsciiString MapCache::getMapDir() const
{
	return AsciiString("Maps");
}
