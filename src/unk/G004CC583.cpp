// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004CC583 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/ModelConditionAudioLoopClientBehaviorModuleData.h"
void Rva004CC371Parse(INI *ini, void *instance, void *store, const void *userData);
static const FieldParse s_modelConditionAudioLoopClientBehaviorModuleDataFieldParse[] =
{
	{ "ModelCondition", Rva004CC371Parse, 0, 0x8 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004CC583 size=17 name=?buildFieldParse@ModelConditionAudioLoopClientBehaviorModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void ModelConditionAudioLoopClientBehaviorModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_modelConditionAudioLoopClientBehaviorModuleDataFieldParse, 0);
}

// FUNCTION: BFME2 0x004CC5AA size=80 name=??1TerrainResourceClientBehavior@@UAE@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
