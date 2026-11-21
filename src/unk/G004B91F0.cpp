// cl: /O1
// stlport46
#include "Common/INI.h"
#include "GameLogic/Module/ExperienceLevelCreateModuleData.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004B91F0 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// Field parse table for ExperienceLevelCreateModuleData (decoded from retail image).
static const FieldParse s_experienceLevelCreateModuleDataFieldParse[] =
{
	{ "LevelToGrant", INI::parseInt, 0, 0x8 },
	{ "MPOnly", INI::parseBool, 0, 0xC },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004B91F0 size=17 name=?buildFieldParse@ExperienceLevelCreateModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void ExperienceLevelCreateModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_experienceLevelCreateModuleDataFieldParse, 0);
}

