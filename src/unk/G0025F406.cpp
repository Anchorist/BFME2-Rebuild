// cl: /O1 /arch:SSE2
// Portions derived from Command & Conquer Generals Zero Hour, (c) Electronic Arts Inc., GPL-3.0-or-later; see LICENSE and NOTICE.
#include "Common/Coord2D.h"
#include "Common/Coord3D.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G0025F406 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x0025F406 size=589 name=?ClipLine2D@@YA_NPAUICoord2D@@000PAUIRegion2D@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0025F653 size=274 name=?IntersectLine2D@@YA_NPBVCoord2D@@000PAV1@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0025F765 size=89 name=?PointInsideArea2D@@YA_NPBVCoord2D@@0H@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0025F7BE size=58 name=?Coord3DInsideRect2D@@YA_NPBVCoord3D@@PBVCoord2D@@1@Z evidence=X:retail PE exports class Coord3D: ??0Matrix4D@@QAE@ABVCoord3D@@@Z tier=B hypothesis:mm1-gap-unit
Bool Coord3DInsideRect2D(const Coord3D *inputPoint, const Coord2D *tl, const Coord2D *br)
{
	if (inputPoint->x >= tl->x && inputPoint->x <= br->x && inputPoint->y >= tl->y && inputPoint->y <= br->y)
		return TRUE;
	return FALSE;
}
// FUNCTION: BFME2 0x0025F7F8 size=117 name=?ScaleRect2D@@YAXPAVCoord2D@@0M@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void ScaleRect2D(Coord2D *tl, Coord2D *br, Real scaleFactor)
{
	Real deltaWidth = (br->x - tl->x) * (scaleFactor - 1.0f) * 0.5f;
	Real deltaHeight = (br->y - tl->y) * (scaleFactor - 1.0f) * 0.5f;
	tl->x -= deltaWidth;
	tl->y -= deltaHeight;
	br->x += deltaWidth;
	br->y += deltaHeight;
}
// FUNCTION: BFME2 0x0025F86D size=169 name=?PointInsideArea2D@@YA_NPBVCoord3D@@0H@Z evidence=X:retail PE exports class Coord3D: ??0Matrix4D@@QAE@ABVCoord3D@@@Z tier=B hypothesis:mm1-gap-unit
