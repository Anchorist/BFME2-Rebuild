// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004910E7 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/DamageFieldUpdateModuleData.h"
static const FieldParse s_damageFieldUpdateModuleDataFieldParse[] =
{
	{ "Radius", INI::parseInt, 0, 0x10 },
	{ "ObjectFilter", iniParseObjectFilter, 0, 0x14 },
	{ "RequiredUpgrade", INI::parseAsciiString, 0, 0x18 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004910E7 size=27 name=?buildFieldParse@DamageFieldUpdateModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void DamageFieldUpdateModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	FireWeaponUpdateModuleData::buildFieldParse(parse);
	parse.add(s_damageFieldUpdateModuleDataFieldParse, 0);
}

// FUNCTION: BFME2 0x00491102 size=76 name=??0DamageFieldUpdateModuleData@@QAE@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0049116A size=68 name=??1DamageFieldUpdateModuleData@@UAE@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
