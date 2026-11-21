// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004C8FD7 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/CritterEmitterUpdateModuleData.h"
void iniParseFXListVec(INI *ini, void *instance, void *store, const void *userData);
static const FieldParse s_critterEmitterUpdateModuleDataFieldParse[] =
{
	{ "FX", iniParseFXListVec, 0, 0x8 },
	{ "ReloadTime", INI::parseDurationUnsignedInt, 0, 0x20 },
	{ "SpawnObject", INI::Rva004C8F94_ParseSpawnObject, 0, 0x0 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004C8FD7 size=17 name=?buildFieldParse@CritterEmitterUpdateModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void CritterEmitterUpdateModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_critterEmitterUpdateModuleDataFieldParse, 0);
}

