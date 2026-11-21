// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G00254F90 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "GameLogic/Module/GarrisonContainModuleData.h"
#include "Common/INI.h"
// FUNCTION: BFME2 0x00254F90 size=84 name=?friend_newModuleData@GarrisonContainModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *GarrisonContainModuleData::friend_newModuleData(INI *ini)
{
	GarrisonContainModuleData *data = new GarrisonContainModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, GarrisonContainModuleData::buildFieldParse);
	return data;
}
