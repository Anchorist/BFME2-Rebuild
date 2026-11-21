// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004AFC5F name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/RespawnUpdateModuleData.h"
#include "GameLogic/Module/RespawnUpdate.h"
// FUNCTION: BFME2 0x004AFC5F size=524 name=?iniParseDefaultRule@RespawnUpdate@@SAXPAVINI@@PAX1PBX@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x004AFE6C size=742 name=?iniParseNewRuleForLevel@RespawnUpdate@@SAXPAVINI@@PAX1PBX@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
static const FieldParse s_respawnUpdateModuleDataFieldParse[] =
{
	{ "DeathAnim", BitFlags<591>::parseFromINI, 0, 0xC },
	{ "DeathFX", INI::parseFXList, 0, 0xF0 },
	{ "DeathAnimationTime", INI::parseDurationUnsignedInt, 0, 0xFC },
	{ "InitialSpawnAnim", BitFlags<591>::parseFromINI, 0, 0xA4 },
	{ "InitialSpawnFX", INI::parseFXList, 0, 0xF8 },
	{ "InitialSpawnAnimationTime", INI::parseDurationUnsignedInt, 0, 0x104 },
	{ "RespawnAnim", BitFlags<591>::parseFromINI, 0, 0x58 },
	{ "RespawnFX", INI::parseFXList, 0, 0xF4 },
	{ "RespawnAnimationTime", INI::parseDurationUnsignedInt, 0, 0x100 },
	{ "AutoRespawnAtObjectFilter", iniParseObjectFilter, 0, 0x8 },
	{ "RespawnRules", RespawnUpdate::iniParseDefaultRule, 0, 0x10C },
	{ "RespawnEntry", RespawnUpdate::iniParseNewRuleForLevel, 0, 0x10C },
	{ "ButtonImage", INI::parseAsciiString, 0, 0x118 },
	{ "RespawnAsTemplate", INI::parseAsciiString, 0, 0x11C },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004B0153 size=17 name=?buildFieldParse@RespawnUpdateModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void RespawnUpdateModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_respawnUpdateModuleDataFieldParse, 0);
}

