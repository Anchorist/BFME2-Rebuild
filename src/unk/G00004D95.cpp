// cl: /O1 /arch:SSE2
// Portions derived from Command & Conquer Generals Zero Hour, (c) Electronic Arts Inc., GPL-3.0-or-later; see LICENSE and NOTICE.
#include "Common/RGBColor.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G00004D95 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x00004D95 size=58 name=?length@ICoord3D@@QBEHXZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00004DCF size=11 name=?zero@ICoord3D@@QAEXXZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00004DDA size=6 name=?width@Region3D@@QBEMXZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00004DE0 size=7 name=?height@Region3D@@QBEMXZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00004DE7 size=7 name=?depth@Region3D@@QBEMXZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00004DEE size=33 name=?zero@Region3D@@QAEXXZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00004E0F size=55 name=?isInRegionNoZ@Region3D@@QBE_NPBVCoord3D@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00004E46 size=77 name=?isInRegionWithZ@Region3D@@QBE_NPBVCoord3D@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00004E93 size=6 name=?width@IRegion3D@@QBEHXZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00004E99 size=7 name=?height@IRegion3D@@QBEHXZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00004EA0 size=7 name=?depth@IRegion3D@@QBEHXZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00004EA7 size=56 name=?getAsInt@RGBColor@@QBEHXZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Int RGBColor::getAsInt() const
{
	return ((((Int)(red * 255.0) << 8) | (Int)(green * 255.0)) << 8) | (Int)(blue * 255.0);
}
// FUNCTION: BFME2 0x00004EDF size=76 name=?setFromInt@RGBColor@@QAEXH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void RGBColor::setFromInt(Int color) throw()
{
	red = ((color >> 16) & 0xFF) / 255.0f;
	green = ((color >> 8) & 0xFF) / 255.0f;
	blue = (color & 0xFF) / 255.0f;
}
