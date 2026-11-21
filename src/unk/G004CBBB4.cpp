// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004CBBB4 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/UpgradeSoundSelectorClientBehaviorModuleData.h"
static const FieldParse s_upgradeSoundSelectorClientBehaviorModuleDataFieldParse[] =
{
	{ "SoundUpgrade", UpgradeSoundSelectorClientBehaviorModuleData::parseSoundUpgrade, 0, 0x0 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004CBBB4 size=17 name=?buildFieldParse@UpgradeSoundSelectorClientBehaviorModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void UpgradeSoundSelectorClientBehaviorModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_upgradeSoundSelectorClientBehaviorModuleDataFieldParse, 0);
}

// FUNCTION: BFME2 0x004CBBC5 size=7 name=?get@Rva004CBBC5FloatField@@QBEMXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x004CBBCC size=7 name=?get@Rva004CBBCCByteField@@QBEEXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x004CBBD3 size=33 name=?parseVoicePriority@RandomSoundSelectorClientBehaviorModuleData@@SAXPAVINI@@PAX1PBX@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x004CBBF4 size=21 name=?rva004CBBF4@Rva004CBBF4@@QBE_NPAH@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x004CBC09 size=34 name=?buildFieldParse@RandomSoundSelectorClientBehaviorModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
