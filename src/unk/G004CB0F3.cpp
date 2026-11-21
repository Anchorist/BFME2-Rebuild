// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004CB0F3 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/ModelConditionSoundSelectorClientBehaviorModuleData.h"
void Rva004CB047Parse(INI *ini, void *instance, void *store, const void *userData);
static const FieldParse s_modelConditionSoundSelectorClientBehaviorModuleDataFieldParse[] =
{
	{ "SoundState", Rva004CB047Parse, 0, 0x0 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004CB0F3 size=17 name=?buildFieldParse@ModelConditionSoundSelectorClientBehaviorModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void ModelConditionSoundSelectorClientBehaviorModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_modelConditionSoundSelectorClientBehaviorModuleDataFieldParse, 0);
}

// FUNCTION: BFME2 0x004CB104 size=33 name=?parseVoicePriority@UpgradeSoundSelectorClientBehaviorModuleData@@SAXPAVINI@@PAX1PBX@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x004CB125 size=21 name=?rva004CB125@Rva004CB125@@QBE_NPAH@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x004CB13A size=14 name=?get@Rva004CB13ADivMovField@@QBEHXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
