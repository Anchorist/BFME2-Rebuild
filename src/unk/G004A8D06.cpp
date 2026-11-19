// cl: /O1
#include "GameLogic/Module/DelayedLuaEventUpdateModuleData.h"
#include "Common/INI/FieldParse.h"

// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004A8D06 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.

// This module has no settings beyond its base module data.
static const FieldParse s_delayedLuaEventFields[] =
{
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004A8D06 size=17 name=?buildFieldParse@DelayedLuaEventUpdateModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void DelayedLuaEventUpdateModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_delayedLuaEventFields, 0);
}
