// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004915B5 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/MonitorConditionUpdateModuleData.h"
static const FieldParse s_monitorConditionUpdateModuleDataFieldParse[] =
{
	{ "ModelConditionFlags", BitFlags<591>::parseFromINI, 0, 0x8 },
	{ "ModelConditionCommandSet", INI::parseAsciiString, 0, 0x54 },
	{ "WeaponSetFlags", BitFlags<104>::parseFromINI, 0, 0x58 },
	{ "WeaponToggleCommandSet", INI::parseAsciiString, 0, 0x68 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004915B5 size=17 name=?buildFieldParse@MonitorConditionUpdateModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void MonitorConditionUpdateModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_monitorConditionUpdateModuleDataFieldParse, 0);
}

