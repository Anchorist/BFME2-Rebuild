// cl: /O1
// stlport46
#include "Common/INI.h"
#include "GameLogic/Module/SpawnUnitBehaviorModuleData.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004B8840 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// Field parse table for SpawnUnitBehaviorModuleData (decoded from retail image).
static const FieldParse s_spawnUnitBehaviorModuleDataFieldParse[] =
{
	{ "UnitName", INI::parseAsciiString, 0, 0x8 },
	{ "UnitCommand", INI::parseAsciiString, 0, 0xC },
	{ "SpawnOnce", INI::parseBool, 0, 0x1C },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004B8840 size=17 name=?buildFieldParse@SpawnUnitBehaviorModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void SpawnUnitBehaviorModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_spawnUnitBehaviorModuleDataFieldParse, 0);
}

// FUNCTION: BFME2 0x004B8851 size=30 name=?rva004B8851@SpawnUnitBehavior@@UBE?AVAsciiString@@XZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x004B886F size=341 name=?update@SpawnUnitBehavior@@UAE?AW4UpdateSleepTime@@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
