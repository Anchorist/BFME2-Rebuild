// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004B60D5 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include <stddef.h>
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/SpellRechargeModifierUpgradeModuleData.h"
#include "GameLogic/Module/UpgradeMuxData.h"
// FUNCTION: BFME2 0x004B60D5 size=37 name=?Rva004B60D5_ParsePercentage@INI@@SAXPAV1@PAX1PBX@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x004B60FA size=34 name=?buildFieldParse@SpellRechargeModifierUpgradeModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
static const FieldParse s_spellRechargeModifierUpgradeModuleDataFieldParse[] =
{
	{ "Percentage", INI::Rva004B60D5_ParsePercentage, 0, offsetof(SpellRechargeModifierUpgradeModuleData, m_percentage) },
	{ "StartsActive", INI::parseBool, 0, offsetof(SpellRechargeModifierUpgradeModuleData, m_startsActive) },
	{ "LabelForPalantirString", INI::parseAsciiString, 0, offsetof(SpellRechargeModifierUpgradeModuleData, m_labelForPalantirString) },
	{ 0, 0, 0, 0 }
};

void SpellRechargeModifierUpgradeModuleData::buildFieldParse(MultiIniFieldParse &p)
{
	p.add(UpgradeMuxData::getFieldParse(), 0x8);
	p.add(s_spellRechargeModifierUpgradeModuleDataFieldParse, 0);
}

