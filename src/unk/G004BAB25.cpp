// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004BAB25 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/ReflectDamageModuleData.h"
static const FieldParse s_reflectDamageModuleDataFieldParse[] =
{
	{ "DamageTypesToReflect", INI::parseDamageTypeFlags, 0, 0x8 },
	{ "ReflectDamagePercentage", INI::parsePercentToReal, 0, 0xC },
	{ "MinimumDamageToReflect", INI::parseReal, 0, 0x10 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004BAB25 size=17 name=?buildFieldParse@ReflectDamageModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void ReflectDamageModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_reflectDamageModuleDataFieldParse, 0);
}

