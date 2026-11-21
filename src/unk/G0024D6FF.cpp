// cl: /O1
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G0024D6FF name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "GameLogic/Module/PickupStuffUpdateModuleData.h"
#include "Common/INI.h"
#include "GameLogic/Module/PickupStuffUpdate.h"
#include "GameLogic/Module/AttachUpdate.h"
#include "GameLogic/Module/MonitorConditionUpdate.h"
#include "GameLogic/Module/DamageFieldUpdate.h"
#include "GameLogic/Module/StrafeAreaUpdateModuleData.h"
#include "GameLogic/Module/StrafeAreaUpdate.h"
#include "GameLogic/Module/AttachUpdateModuleData.h"
#include "GameLogic/Module/MonitorConditionUpdateModuleData.h"
#include "GameLogic/Module/DamageFieldUpdateModuleData.h"
// Module creators. Retail registers each module class with a static friend_newModuleInstance that allocates the
// module for a thing and its module data, and each module data class with a static friend_newModuleData that
// allocates the data and, when an INI block is open, fills it from the class's buildFieldParse table. The bodies
// below are those two shapes. A class whose creator is not here yet has no real header, lacks the constructor or
// buildFieldParse declaration, or did not compile with its current header (the usual cause is a pure virtual that
// the header does not override yet); its row stays unwritten.
// FUNCTION: BFME2 0x0024D6FF size=56 name=?friend_newModuleInstance@StrafeAreaUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *StrafeAreaUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new StrafeAreaUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024D737 size=81 name=?friend_newModuleData@StrafeAreaUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *StrafeAreaUpdateModuleData::friend_newModuleData(INI *ini)
{
	StrafeAreaUpdateModuleData *data = new StrafeAreaUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, StrafeAreaUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024D788 size=56 name=?friend_newModuleInstance@DamageFieldUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *DamageFieldUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new DamageFieldUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024D7C0 size=81 name=?friend_newModuleData@DamageFieldUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *DamageFieldUpdateModuleData::friend_newModuleData(INI *ini)
{
	DamageFieldUpdateModuleData *data = new DamageFieldUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, DamageFieldUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024D811 size=56 name=?friend_newModuleInstance@MonitorConditionUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *MonitorConditionUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new MonitorConditionUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024D849 size=81 name=?friend_newModuleData@MonitorConditionUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *MonitorConditionUpdateModuleData::friend_newModuleData(INI *ini)
{
	MonitorConditionUpdateModuleData *data = new MonitorConditionUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, MonitorConditionUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024D89A size=56 name=?friend_newModuleInstance@AttachUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *AttachUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new AttachUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024D8D2 size=81 name=?friend_newModuleData@AttachUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *AttachUpdateModuleData::friend_newModuleData(INI *ini)
{
	AttachUpdateModuleData *data = new AttachUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, AttachUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024D923 size=56 name=?friend_newModuleInstance@PickupStuffUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *PickupStuffUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new PickupStuffUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024D95B size=81 name=?friend_newModuleData@PickupStuffUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *PickupStuffUpdateModuleData::friend_newModuleData(INI *ini)
{
	PickupStuffUpdateModuleData *data = new PickupStuffUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, PickupStuffUpdateModuleData::buildFieldParse);
	return data;
}
