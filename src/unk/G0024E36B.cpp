// cl: /O1
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G0024E36B name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "GameLogic/Module/SupplyCenterProductionExitUpdate.h"
#include "GameLogic/Module/StructureToppleUpdate.h"
#include "GameLogic/Module/StructureCollapseUpdate.h"
#include "GameLogic/Module/HijackerUpdate.h"
#include "GameLogic/Module/InvisibilityUpdate.h"
#include "GameLogic/Module/StealthUpdateModuleData.h"
#include "Common/INI.h"
#include "GameLogic/Module/StealthUpdate.h"
#include "GameLogic/Module/BroadcastStealthUpdate.h"
#include "GameLogic/Module/SlavedUpdate.h"
#include "GameLogic/Module/MonsterDockUpdateModuleData.h"
#include "GameLogic/Module/MonsterDockUpdate.h"
#include "GameLogic/Module/RepairDockUpdate.h"
#include "GameLogic/Module/SupplyCenterDockUpdate.h"
#include "GameLogic/Module/RadarUpdate.h"
#include "GameLogic/Module/QueueProductionExitUpdate.h"
#include "GameLogic/Module/ProneUpdateModuleData.h"
#include "GameLogic/Module/ProductionUpdateModuleData.h"
#include "GameLogic/Module/GiveUpgradeUpdateModuleData.h"
#include "GameLogic/Module/GiveUpgradeUpdate.h"
#include "GameLogic/Module/RadiateFearUpdateModuleData.h"
#include "GameLogic/Module/RadiateFearUpdate.h"
#include "GameLogic/Module/AttributeModifierAuraUpdateModuleData.h"
#include "GameLogic/Module/AttributeModifierAuraUpdate.h"
#include "GameLogic/Module/OCLUpdateModuleData.h"
#include "GameLogic/Module/OCLUpdate.h"
#include "GameLogic/Module/AutoDepositUpdate.h"
#include "GameLogic/Module/SpecialEnemySenseUpdate.h"
// FUNCTION: BFME2 0x0024E36B size=56 name=?friend_newModuleInstance@LifetimeUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024E3A3 size=81 name=?friend_newModuleData@LifetimeUpdate@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024E3F4 size=56 name=?friend_newModuleInstance@OneRingPenaltyUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024E42C size=81 name=?friend_newModuleData@OneRingPenaltyUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024E47D size=56 name=?friend_newModuleInstance@SpecialEnemySenseUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *SpecialEnemySenseUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new SpecialEnemySenseUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024E4B5 size=56 name=?friend_newModuleInstance@RadiusDecalUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024E4ED size=56 name=?friend_newModuleInstance@AutoDepositUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *AutoDepositUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new AutoDepositUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024E525 size=59 name=?friend_newModuleInstance@HordeAIUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024E560 size=59 name=?friend_newModuleInstance@HordeWorkerAIUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024E59B size=56 name=?friend_newModuleInstance@OCLUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *OCLUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new OCLUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024E5D3 size=81 name=?friend_newModuleData@OCLUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *OCLUpdateModuleData::friend_newModuleData(INI *ini)
{
	OCLUpdateModuleData *data = new OCLUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, OCLUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024E624 size=56 name=?friend_newModuleInstance@AttributeModifierAuraUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *AttributeModifierAuraUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new AttributeModifierAuraUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024E65C size=84 name=?friend_newModuleData@AttributeModifierAuraUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *AttributeModifierAuraUpdateModuleData::friend_newModuleData(INI *ini)
{
	AttributeModifierAuraUpdateModuleData *data = new AttributeModifierAuraUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, AttributeModifierAuraUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024E6B0 size=56 name=?friend_newModuleInstance@RadiateFearUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *RadiateFearUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new RadiateFearUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024E6E8 size=84 name=?friend_newModuleData@RadiateFearUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *RadiateFearUpdateModuleData::friend_newModuleData(INI *ini)
{
	RadiateFearUpdateModuleData *data = new RadiateFearUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, RadiateFearUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024E73C size=56 name=?friend_newModuleInstance@PhysicsBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024E774 size=81 name=?friend_newModuleData@PhysicsBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024E7C5 size=59 name=?friend_newModuleInstance@GiveUpgradeUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *GiveUpgradeUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new GiveUpgradeUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024E800 size=84 name=?friend_newModuleData@GiveUpgradeUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *GiveUpgradeUpdateModuleData::friend_newModuleData(INI *ini)
{
	GiveUpgradeUpdateModuleData *data = new GiveUpgradeUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, GiveUpgradeUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024E854 size=59 name=?friend_newModuleInstance@ProductionUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024E88F size=81 name=?friend_newModuleData@ProductionUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *ProductionUpdateModuleData::friend_newModuleData(INI *ini)
{
	ProductionUpdateModuleData *data = new ProductionUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, ProductionUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024E8E0 size=56 name=?friend_newModuleInstance@ProneUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024E918 size=81 name=?friend_newModuleData@ProneUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *ProneUpdateModuleData::friend_newModuleData(INI *ini)
{
	ProneUpdateModuleData *data = new ProneUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, ProneUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024E969 size=56 name=?friend_newModuleInstance@QueueProductionExitUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *QueueProductionExitUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new QueueProductionExitUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024E9A1 size=56 name=?friend_newModuleInstance@RadarUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *RadarUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new RadarUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024E9D9 size=59 name=?friend_newModuleInstance@SupplyCenterDockUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *SupplyCenterDockUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new SupplyCenterDockUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024EA14 size=81 name=?friend_newModuleData@SupplyCenterDockUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024EA65 size=59 name=?friend_newModuleInstance@RepairDockUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *RepairDockUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new RepairDockUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024EAA0 size=81 name=?friend_newModuleData@RepairDockUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024EAF1 size=59 name=?friend_newModuleInstance@MonsterDockUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *MonsterDockUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new MonsterDockUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024EB2C size=81 name=?friend_newModuleData@MonsterDockUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *MonsterDockUpdateModuleData::friend_newModuleData(INI *ini)
{
	MonsterDockUpdateModuleData *data = new MonsterDockUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, MonsterDockUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024EB7D size=56 name=?friend_newModuleInstance@SlavedUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *SlavedUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new SlavedUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024EBB5 size=56 name=?friend_newModuleInstance@StealthDetectorUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024EBED size=56 name=?friend_newModuleInstance@BroadcastStealthUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *BroadcastStealthUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new BroadcastStealthUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024EC25 size=59 name=?friend_newModuleInstance@StealthUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *StealthUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new StealthUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024EC60 size=84 name=?friend_newModuleData@StealthUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *StealthUpdateModuleData::friend_newModuleData(INI *ini)
{
	StealthUpdateModuleData *data = new StealthUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, StealthUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024ECB4 size=56 name=?friend_newModuleInstance@InvisibilityUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *InvisibilityUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new InvisibilityUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024ECEC size=59 name=?friend_newModuleInstance@SpawnPointProductionExitUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024ED27 size=56 name=?friend_newModuleInstance@HijackerUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *HijackerUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new HijackerUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024ED5F size=56 name=?friend_newModuleInstance@FadeAndDieOrnamentUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024ED97 size=56 name=?friend_newModuleInstance@StructureCollapseUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *StructureCollapseUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new StructureCollapseUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024EDCF size=56 name=?friend_newModuleInstance@RubbleRiseUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024EE07 size=56 name=?friend_newModuleInstance@StructureToppleUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *StructureToppleUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new StructureToppleUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024EE3F size=56 name=?friend_newModuleInstance@SupplyCenterProductionExitUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *SupplyCenterProductionExitUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new SupplyCenterProductionExitUpdate(thing, moduleData);
}
