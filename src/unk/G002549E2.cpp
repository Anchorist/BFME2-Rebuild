// cl: /O1
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G002549E2 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "GameLogic/Module/TransitionDamageFXModuleData.h"
#include "Common/INI.h"
// FUNCTION: BFME2 0x002549E2 size=84 name=?friend_newModuleData@TransitionDamageFXModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *TransitionDamageFXModuleData::friend_newModuleData(INI *ini)
{
	TransitionDamageFXModuleData *data = new TransitionDamageFXModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, TransitionDamageFXModuleData::buildFieldParse);
	return data;
}
