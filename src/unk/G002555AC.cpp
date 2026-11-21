// cl: /O1
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G002555AC name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "GameLogic/Module/CommandSetUpgradeModuleData.h"
#include "Common/INI.h"
// FUNCTION: BFME2 0x002555AC size=85 name=??0FadeAndDieOrnamentUpdateModuleData@@QAE@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00255601 size=81 name=?friend_newModuleData@FadeAndDieOrnamentUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00255652 size=70 name=??0CommandSetUpgradeModuleData@@QAE@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00255698 size=84 name=?friend_newModuleData@CommandSetUpgradeModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *CommandSetUpgradeModuleData::friend_newModuleData(INI *ini)
{
	CommandSetUpgradeModuleData *data = new CommandSetUpgradeModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, CommandSetUpgradeModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x002556EC size=84 name=?friend_newModuleData@StatusBitsUpgradeIfEldestKindofModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0025575C size=57 name=??1StatusBitsUpgradeIfEldestKindofModuleData@@UAE@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
