// cl: /O1
// stlport46
#include "Common/INI.h"
#include "GameLogic/Module/StopSpecialPowerModuleData.h"
#include "GameLogic/Module/SpecialPowerModule.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004C64EE name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x004C64EE size=154 name=?update@SiegeDeployHordeSpecialPower@@UAE?AW4UpdateSleepTime@@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x004C6588 size=457 name=?initiateIntentToDoSpecialPower@SiegeDeployHordeSpecialPower@@UAEXPBVSpecialPowerTemplate@@PBVObject@@PBVCoord3D@@IPBVWaypoint@@@Z evidence=X:retail PE exports class Coord3D: ??0Matrix4D@@QAE@ABVCoord3D@@@Z tier=B hypothesis:mm1-gap-unit
// Field parse table for StopSpecialPowerModuleData (decoded from retail image).
static const FieldParse s_stopSpecialPowerModuleDataFieldParse[] =
{
	{ "StopPowerTemplate", INI::parseSpecialPowerTemplate, 0, 0x7C },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004C6751 size=27 name=?buildFieldParse@StopSpecialPowerModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void StopSpecialPowerModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	SpecialPowerModuleData::buildFieldParse(parse);
	parse.add(s_stopSpecialPowerModuleDataFieldParse, 0);
}

