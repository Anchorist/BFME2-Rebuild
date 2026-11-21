// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004598E1 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/SiegeDockingBehaviorModuleData.h"
static const FieldParse s_siegeDockingBehaviorModuleDataFieldParse[] =
{
	{ "DUMMY", INI::parseInt, 0, 0x8 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004598E1 size=17 name=?buildFieldParse@SiegeDockingBehaviorModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void SiegeDockingBehaviorModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_siegeDockingBehaviorModuleDataFieldParse, 0);
}

