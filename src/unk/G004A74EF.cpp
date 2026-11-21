// cl: /O1
// stlport46
#include "Common/INI.h"
#include "GameLogic/Module/MissileUpdateModuleData.h"
#include "GameLogic/Module/BezierProjectileBehaviorModuleData.h"
#include "Common/BitFlags.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004A74EF name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// Field parse table for MissileUpdateModuleData (decoded from retail image).
static const FieldParse s_missileUpdateModuleDataFieldParse[] =
{
	{ "FuelLifetime", INI::parseDurationUnsignedInt, 0, 0xC4 },
	{ "IgnitionDelay", INI::parseDurationUnsignedInt, 0, 0xC8 },
	{ "DistanceToTravelBeforeTurning", INI::parseReal, 0, 0xCC },
	{ "DistanceToTargetBeforeDiving", INI::parseReal, 0, 0xD0 },
	{ "IgnitionFX", INI::parseFXList, 0, 0xD4 },
	{ "DetonateOnNoFuel", INI::parseBool, 0, 0xD8 },
	{ "ExhaustTemplate", INI::parseAsciiString, 0, 0x11C },
	{ "GarrisonHitKillRequiredKindOf", KindOfMaskType::parseFromINI, 0, 0xE0 },
	{ "GarrisonHitKillForbiddenKindOf", KindOfMaskType::parseFromINI, 0, 0xFC },
	{ "GarrisonHitKillCount", INI::parseUnsignedInt, 0, 0xDC },
	{ "GarrisonHitKillFX", INI::parseFXList, 0, 0x118 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004A74EF size=27 name=?buildFieldParse@MissileUpdateModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void MissileUpdateModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	BezierProjectileBehaviorModuleData::buildFieldParse(parse);
	parse.add(s_missileUpdateModuleDataFieldParse, 0);
}

