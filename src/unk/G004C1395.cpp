// cl: /O1
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004C1395 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/DelayedDeathBodyModuleData.h"
// FUNCTION: BFME2 0x004C1395 size=330 name=?internalChangeHealth@RespawnBody@@UAEXMPAVDamageInfo@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x004C14DF size=110 name=??0RespawnBodyModuleData@@QAE@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x004C1569 size=53 name=??1RespawnBodyModuleData@@UAE@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
static const FieldParse s_delayedDeathBodyModuleDataFieldParse[] =
{
	{ "DelayedDeathTime", INI::parseDurationUnsignedInt, 0, 0x6C },
	{ "ImmortalUntilDeathTime", INI::parseBool, 0, 0x70 },
	{ "DoHealthCheck", INI::parseBool, 0, 0x78 },
	{ "InvulnerableFX", INI::parseFXList, 0, 0x74 },
	{ "DelayedDeathPrerequisiteUpgrade", INI::parseUpgradeTemplate, 0, 0x7C },
};

// FUNCTION: BFME2 0x004C159E size=27 name=?buildFieldParse@DelayedDeathBodyModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void DelayedDeathBodyModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	RespawnBodyModuleData::buildFieldParse(parse);
	parse.add(s_delayedDeathBodyModuleDataFieldParse, 0);
}

