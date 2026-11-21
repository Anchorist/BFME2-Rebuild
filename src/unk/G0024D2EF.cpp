// cl: /O1
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G0024D2EF name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "GameLogic/Module/SiegeAIUpdateModuleData.h"
#include "Common/INI.h"
#include "GameLogic/Module/SiegeAIUpdate.h"
#include "GameLogic/Module/LargeGroupBonusUpdateModuleData.h"
#include "GameLogic/Module/LargeGroupBonusUpdate.h"
#include "GameLogic/Module/GiantBirdAIUpdateModuleData.h"
// FUNCTION: BFME2 0x0024D2EF size=59 name=?friend_newModuleInstance@GiantBirdAIUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024D32A size=84 name=?friend_newModuleData@GiantBirdAIUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *GiantBirdAIUpdateModuleData::friend_newModuleData(INI *ini)
{
	GiantBirdAIUpdateModuleData *data = new GiantBirdAIUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, GiantBirdAIUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024D37E size=56 name=?friend_newModuleInstance@HeightDieUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024D3B6 size=81 name=?friend_newModuleData@HeightDieUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024D407 size=56 name=?friend_newModuleInstance@LargeGroupBonusUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *LargeGroupBonusUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new LargeGroupBonusUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024D43F size=81 name=?friend_newModuleData@LargeGroupBonusUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *LargeGroupBonusUpdateModuleData::friend_newModuleData(INI *ini)
{
	LargeGroupBonusUpdateModuleData *data = new LargeGroupBonusUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, LargeGroupBonusUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024D490 size=59 name=?friend_newModuleInstance@SiegeAIUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *SiegeAIUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new SiegeAIUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024D4CB size=81 name=?friend_newModuleData@SiegeAIUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *SiegeAIUpdateModuleData::friend_newModuleData(INI *ini)
{
	SiegeAIUpdateModuleData *data = new SiegeAIUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, SiegeAIUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024D51C size=6 name=?Rva0024D51CGet@@YAHXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// Returns a fixed constant (a flag mask or size); its role in the original is not recovered, so the ledger name stays.
int Rva0024D51CGet()
{
	return 2048;
}
// FUNCTION: BFME2 0x0024D522 size=56 name=?friend_newModuleInstance@LaserUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024D55A size=81 name=?friend_newModuleData@LaserUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
