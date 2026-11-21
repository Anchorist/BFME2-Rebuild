// cl: /O1
// stlport46
#include "Common/INI.h"
#include "GameLogic/Module/GiveUpgradeUpdateModuleData.h"
#include "GameLogic/Module/SpecialAbilityUpdateModuleData.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G0049C391 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// Field parse table for GiveUpgradeUpdateModuleData (decoded from retail image).
static const FieldParse s_giveUpgradeUpdateModuleDataFieldParse[] =
{
	{ "GiveUpgradeEffect", INI::parseFXList, 0, 0xD4 },
	{ "SpawnOutFX", INI::parseFXList, 0, 0xD8 },
	{ "FadeOutSpeed", INI::parseReal, 0, 0xDC },
	{ "DeliverUpgrade", INI::parseBool, 0, 0xE0 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x0049C391 size=27 name=?buildFieldParse@GiveUpgradeUpdateModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void GiveUpgradeUpdateModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	SpecialAbilityUpdateModuleData::buildFieldParse(parse);
	parse.add(s_giveUpgradeUpdateModuleDataFieldParse, 0);
}

