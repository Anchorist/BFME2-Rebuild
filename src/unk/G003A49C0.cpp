// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G003A49C0 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/SpawnedModelConditionCreateModuleData.h"
class Rva003A47F3Owner;
void Rva003A47F3Parse(INI *ini, Rva003A47F3Owner *owner);
static const FieldParse s_spawnedModelConditionCreateModuleDataFieldParse[] =
{
	{ "SpawnerTrigger", (INIFieldParseProc)Rva003A47F3Parse, 0, 0x0 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x003A49C0 size=17 name=?buildFieldParse@SpawnedModelConditionCreateModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void SpawnedModelConditionCreateModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_spawnedModelConditionCreateModuleDataFieldParse, 0);
}

