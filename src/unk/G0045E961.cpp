// cl: /O1
#include "GameLogic/Module/ShipSlowDeathBehaviorModuleData.h"
#include "Common/INI/FieldParse.h"

// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G0045E961 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.

// The ship module inherits the slow-death fields.
static const FieldParse s_shipSlowDeathFields[] =
{
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x0045E961 size=18 name=??0ShipSlowDeathBehaviorModuleData@@QAE@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ShipSlowDeathBehaviorModuleData::ShipSlowDeathBehaviorModuleData()
{
}

// FUNCTION: BFME2 0x0045E973 size=27 name=?buildFieldParse@ShipSlowDeathBehaviorModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void ShipSlowDeathBehaviorModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	SlowDeathBehaviorModuleData::buildFieldParse(parse);
	parse.add(s_shipSlowDeathFields, 0);
}
