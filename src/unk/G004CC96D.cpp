// cl: /O1
#include <stddef.h>
#include "Common/INI.h"
#include "GameLogic/Module/DominateEnemySpecialPowerModuleData.h"

// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004CC96D name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.

static const FieldParse s_dominateEnemySpecialPowerFields[] =
{
	{ "DominateRadius", INI::parseReal, 0, offsetof(DominateEnemySpecialPowerModuleData, m_dominateRadius) },
	{ "TriggerFX", INI::parseFXList, 0, offsetof(DominateEnemySpecialPowerModuleData, m_triggerFX) },
	{ "DominatedFX", INI::parseFXList, 0, offsetof(DominateEnemySpecialPowerModuleData, m_dominatedFX) },
	{ "PermanentlyConvert", INI::parseBool, 0, offsetof(DominateEnemySpecialPowerModuleData, m_permanentlyConvert) },
	{ "AttributeModifierAffects", iniParseObjectFilter, 0, offsetof(DominateEnemySpecialPowerModuleData, m_attributeModifierAffects) },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004CC96D size=27 name=?buildFieldParse@DominateEnemySpecialPowerModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void DominateEnemySpecialPowerModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	SpecialAbilityUpdateModuleData::buildFieldParse(parse);
	parse.add(s_dominateEnemySpecialPowerFields, 0);
}
