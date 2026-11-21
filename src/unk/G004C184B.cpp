// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004C184B name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/FreeLifeBodyModuleData.h"
static const FieldParse s_freeLifeBodyModuleDataFieldParse[] =
{
	{ "FreeLifeHealthPercent", INI::parsePercentToReal, 0, 0x6C },
	{ "FreeLifeTime", INI::parseDurationUnsignedInt, 0, 0x70 },
	{ "FreeLifeInvincible", INI::parseBool, 0, 0x74 },
	{ "FreeLifePrerequisiteUpgrade", INI::parseUpgradeTemplate, 0, 0x84 },
	{ "FreeLifeAnimAndDuration", INI::iniParseAnimAndDuration, 0, 0x78 },
};

// FUNCTION: BFME2 0x004C184B size=27 name=?buildFieldParse@FreeLifeBodyModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void FreeLifeBodyModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	RespawnBodyModuleData::buildFieldParse(parse);
	parse.add(s_freeLifeBodyModuleDataFieldParse, 0);
}

