// cl: /O1
#include "WW3D2/BFME2MotionChannel.h"
#include <new>

// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G001B20E5 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x001B20E5 size=83 name=?Rva001B20E5Init@@YA_NXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x001B2138 size=22 name=??0BFME2StreamMotionChannel@@QAE@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
BFME2StreamMotionChannel::BFME2StreamMotionChannel()
	: Data(0)
{
}

// FUNCTION: BFME2 0x001B214E size=26 name=??1BFME2StreamMotionChannel@@UAE@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
BFME2StreamMotionChannel::~BFME2StreamMotionChannel()
{
	::operator delete[](Data);
}
