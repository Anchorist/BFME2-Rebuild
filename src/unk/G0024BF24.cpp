// cl: /O1
// stlport46
#include "Common/INI.h"
#include "GameLogic/Module/DeployStyleAIUpdateModuleData.h"
#include "GameLogic/Module/AIUpdate.h"
#include "GameLogic/Module/ProductionQueueHordeContainModuleData.h"
#include "GameLogic/Module/ProductionQueueHordeContain.h"
#include "GameLogic/Module/CitadelSlaughterHordeContainModuleData.h"
#include "GameLogic/Module/CitadelSlaughterHordeContain.h"
#include "GameLogic/Module/SlaughterHordeContainModuleData.h"
#include "GameLogic/Module/SlaughterHordeContain.h"
#include "GameLogic/Module/ShareExperienceBehaviorModuleData.h"
#include "GameLogic/Module/CivilianSpawnUpdateModuleData.h"
#include "GameLogic/Module/CivilianSpawnUpdate.h"
#include "GameLogic/Module/SupplyWarehouseCripplingBehavior.h"
#include "GameLogic/Module/RebuildHoleBehaviorModuleData.h"
#include "GameLogic/Module/RebuildHoleBehavior.h"
#include "GameLogic/Module/PoisonedBehaviorModuleData.h"
#include "GameLogic/Module/FireWeaponWhenDeadBehavior.h"
#include "GameLogic/Module/FireWeaponWhenDamagedBehavior.h"
#include "GameLogic/Module/TerrainResourceBehaviorModuleData.h"
#include "GameLogic/Module/TerrainResourceBehavior.h"
#include "GameLogic/Module/PropagandaTowerBehaviorModuleData.h"
#include "GameLogic/Module/PropagandaTowerBehavior.h"
#include "GameLogic/Module/AnnounceBirthAndDeathBehavior.h"
#include "GameLogic/Module/PassiveAreaEffectBehaviorModuleData.h"
#include "GameLogic/Module/PassiveAreaEffectBehavior.h"
#include "GameLogic/Module/AttributeModifierPoolUpdate.h"
#include "GameLogic/Module/SlaveWatcherBehavior.h"
#include "GameLogic/Module/ReplenishUnitsBehaviorModuleData.h"
#include "GameLogic/Module/ReplenishUnitsBehavior.h"
#include "GameLogic/Module/ClearanceTestingSlowDeathBehaviorModuleData.h"
#include "GameLogic/Module/ClearanceTestingSlowDeathBehavior.h"
#include "GameLogic/Module/SupplyWarehouseCripplingBehaviorModuleData.h"
#include "GameLogic/Module/RebuildHoleExposeDieModuleData.h"
#include "GameLogic/Module/FXListDie.h"
#include "GameLogic/Module/DestroyDie.h"
#include "GameLogic/Module/CrushDie.h"
#include "GameLogic/Module/DamageFilteredCreateObjectDieModuleData.h"
#include "GameLogic/Module/DamageFilteredCreateObjectDie.h"
#include "GameLogic/Module/CreateObjectDieIfEldestKindofModuleData.h"
#include "GameLogic/Module/CreateObjectDieModuleData.h"
#include "GameLogic/Module/CreateCrateDie.h"
#include "GameLogic/Module/RefundDie.h"
#include "GameLogic/Module/SpecialPowerCompletionDie.h"
#include "GameLogic/Module/FireSpreadUpdate.h"
#include "GameLogic/Module/DozerAIUpdateModuleData.h"
#include "GameLogic/Module/DozerAIUpdate.h"
#include "GameLogic/Module/DeletionUpdate.h"
#include "GameLogic/Module/DelayedWeaponSetUpgradeUpdateModuleData.h"
#include "GameLogic/Module/DefaultProductionExitUpdate.h"
#include "GameLogic/Module/AssistedTargetingUpdate.h"
#include "GameLogic/Module/KeepObjectDie.h"
#include "GameLogic/Module/DeployStyleAIUpdate.h"
#include "GameLogic/Module/FloatUpdateModuleData.h"
#include "GameLogic/Module/FloatUpdate.h"
#include "GameLogic/Module/OilSpillUpdate.h"
#include "GameLogic/Module/FireWeaponUpdate.h"
#include "GameLogic/Module/FireSpreadUpdateModuleData.h"
#include "GameLogic/Module/PoisonedBehavior.h"
#include "GameLogic/Module/FlammableUpdateModuleData.h"
#include "GameLogic/Module/FlammableUpdate.h"
#include "GameLogic/Module/DynamicShroudClearingRangeUpdateModuleData.h"
#include "GameLogic/Module/DynamicShroudClearingRangeUpdate.h"
#include "GameLogic/Module/UpgradeDie.h"
#include "GameLogic/Module/RebuildHoleExposeDie.h"
#include "GameLogic/Module/CreateObjectDieIfEldestKindof.h"
#include "GameLogic/Module/OilSpillUpdateModuleData.h"
#include "GameLogic/Module/SlaveWatcherBehaviorModuleData.h"
#include "GameLogic/Module/DelayedWeaponSetUpgradeUpdate.h"
#include "GameLogic/Module/FloodUpdateModuleData.h"
// Module creators. Retail registers each module class with a static friend_newModuleInstance that allocates the
// module for a thing and its module data, and each module data class with a static friend_newModuleData that
// allocates the data and, when an INI block is open, fills it from the class's buildFieldParse table. The bodies
// below are those two shapes. A class whose creator is not here yet has no real header, lacks the constructor or
// buildFieldParse declaration, or did not compile with its current header (the usual cause is a pure virtual that
// the header does not override yet); its row stays unwritten.
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G0024BF24 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x0024BF24 size=56 name=?friend_newModuleInstance@CivilianSpawnUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *CivilianSpawnUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new CivilianSpawnUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024BF5C size=81 name=?friend_newModuleData@CivilianSpawnUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *CivilianSpawnUpdateModuleData::friend_newModuleData(INI *ini)
{
	CivilianSpawnUpdateModuleData *data = new CivilianSpawnUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, CivilianSpawnUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024BFAD size=56 name=?friend_newModuleInstance@ShareExperienceBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024BFE5 size=81 name=?friend_newModuleData@ShareExperienceBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *ShareExperienceBehaviorModuleData::friend_newModuleData(INI *ini)
{
	ShareExperienceBehaviorModuleData *data = new ShareExperienceBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, ShareExperienceBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024C036 size=59 name=?friend_newModuleInstance@SlaughterHordeContain@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *SlaughterHordeContain::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new SlaughterHordeContain(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C071 size=84 name=?friend_newModuleData@SlaughterHordeContainModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *SlaughterHordeContainModuleData::friend_newModuleData(INI *ini)
{
	SlaughterHordeContainModuleData *data = new SlaughterHordeContainModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, SlaughterHordeContainModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024C0C5 size=59 name=?friend_newModuleInstance@CitadelSlaughterHordeContain@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *CitadelSlaughterHordeContain::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new CitadelSlaughterHordeContain(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C100 size=84 name=?friend_newModuleData@CitadelSlaughterHordeContainModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *CitadelSlaughterHordeContainModuleData::friend_newModuleData(INI *ini)
{
	CitadelSlaughterHordeContainModuleData *data = new CitadelSlaughterHordeContainModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, CitadelSlaughterHordeContainModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024C154 size=59 name=?friend_newModuleInstance@ProductionQueueHordeContain@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *ProductionQueueHordeContain::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new ProductionQueueHordeContain(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C18F size=84 name=?friend_newModuleData@ProductionQueueHordeContainModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *ProductionQueueHordeContainModuleData::friend_newModuleData(INI *ini)
{
	ProductionQueueHordeContainModuleData *data = new ProductionQueueHordeContainModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, ProductionQueueHordeContainModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024C1E3 size=56 name=?friend_newModuleInstance@PropagandaTowerBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *PropagandaTowerBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new PropagandaTowerBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C21B size=81 name=?friend_newModuleData@PropagandaTowerBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *PropagandaTowerBehaviorModuleData::friend_newModuleData(INI *ini)
{
	PropagandaTowerBehaviorModuleData *data = new PropagandaTowerBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, PropagandaTowerBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024C26C size=56 name=?friend_newModuleInstance@TerrainResourceBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *TerrainResourceBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new TerrainResourceBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C2A4 size=81 name=?friend_newModuleData@TerrainResourceBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *TerrainResourceBehaviorModuleData::friend_newModuleData(INI *ini)
{
	TerrainResourceBehaviorModuleData *data = new TerrainResourceBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, TerrainResourceBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024C2F5 size=56 name=?friend_newModuleInstance@FireWeaponWhenDamagedBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *FireWeaponWhenDamagedBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new FireWeaponWhenDamagedBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C32D size=6 name=?Rva0024C32DGet@@YAHXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// No retail code or data refers to this function. It follows the creators of FireWeaponWhenDamagedBehavior and returns the bit set 0x85, which looks like a module interface mask;
// nothing ties it to FireWeaponWhenDamagedBehavior, so it keeps its ledger name.
int Rva0024C32DGet()
{
	return 133;
}
// FUNCTION: BFME2 0x0024C333 size=59 name=?friend_newModuleInstance@FireWeaponWhenDeadBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *FireWeaponWhenDeadBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new FireWeaponWhenDeadBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C36E size=56 name=?friend_newModuleInstance@PoisonedBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *PoisonedBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new PoisonedBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C3A6 size=81 name=?friend_newModuleData@PoisonedBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *PoisonedBehaviorModuleData::friend_newModuleData(INI *ini)
{
	PoisonedBehaviorModuleData *data = new PoisonedBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, PoisonedBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024C3F7 size=4 name=?get@Rva0024C3F7Const@@SAHXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024C3FB size=56 name=?friend_newModuleInstance@RebuildHoleBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *RebuildHoleBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new RebuildHoleBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C433 size=81 name=?friend_newModuleData@RebuildHoleBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *RebuildHoleBehaviorModuleData::friend_newModuleData(INI *ini)
{
	RebuildHoleBehaviorModuleData *data = new RebuildHoleBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, RebuildHoleBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024C484 size=56 name=?friend_newModuleInstance@SupplyWarehouseCripplingBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *SupplyWarehouseCripplingBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new SupplyWarehouseCripplingBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C4BC size=81 name=?friend_newModuleData@SupplyWarehouseCripplingBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *SupplyWarehouseCripplingBehaviorModuleData::friend_newModuleData(INI *ini)
{
	SupplyWarehouseCripplingBehaviorModuleData *data = new SupplyWarehouseCripplingBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, SupplyWarehouseCripplingBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024C50D size=56 name=?friend_newModuleInstance@ClearanceTestingSlowDeathBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *ClearanceTestingSlowDeathBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new ClearanceTestingSlowDeathBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C545 size=84 name=?friend_newModuleData@ClearanceTestingSlowDeathBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *ClearanceTestingSlowDeathBehaviorModuleData::friend_newModuleData(INI *ini)
{
	ClearanceTestingSlowDeathBehaviorModuleData *data = new ClearanceTestingSlowDeathBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, ClearanceTestingSlowDeathBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024C599 size=56 name=?friend_newModuleInstance@ReplenishUnitsBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *ReplenishUnitsBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new ReplenishUnitsBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C5D1 size=84 name=?friend_newModuleData@ReplenishUnitsBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *ReplenishUnitsBehaviorModuleData::friend_newModuleData(INI *ini)
{
	ReplenishUnitsBehaviorModuleData *data = new ReplenishUnitsBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, ReplenishUnitsBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024C625 size=59 name=?friend_newModuleInstance@SlaveWatcherBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *SlaveWatcherBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new SlaveWatcherBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C660 size=81 name=?friend_newModuleData@SlaveWatcherBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *SlaveWatcherBehaviorModuleData::friend_newModuleData(INI *ini)
{
	SlaveWatcherBehaviorModuleData *data = new SlaveWatcherBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, SlaveWatcherBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024C6B1 size=59 name=?friend_newModuleInstance@AttributeModifierPoolUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *AttributeModifierPoolUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new AttributeModifierPoolUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C6EC size=56 name=?friend_newModuleInstance@PassiveAreaEffectBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *PassiveAreaEffectBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new PassiveAreaEffectBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C724 size=81 name=?friend_newModuleData@PassiveAreaEffectBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *PassiveAreaEffectBehaviorModuleData::friend_newModuleData(INI *ini)
{
	PassiveAreaEffectBehaviorModuleData *data = new PassiveAreaEffectBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, PassiveAreaEffectBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024C775 size=6 name=?Rva0024C775Get@@YAHXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// No retail code or data refers to this function. It follows the creators of PassiveAreaEffectBehavior and returns the bit set 0x2000, which looks like a module interface mask;
// nothing ties it to PassiveAreaEffectBehavior, so it keeps its ledger name.
int Rva0024C775Get()
{
	return 8192;
}
// FUNCTION: BFME2 0x0024C77B size=56 name=?friend_newModuleInstance@PillageModule@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024C7C7 size=56 name=?friend_newModuleInstance@AnnounceBirthAndDeathBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *AnnounceBirthAndDeathBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new AnnounceBirthAndDeathBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C7FF size=14 name=?clear@Rva005D75BEMask@@QAEXXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024C80D size=12 name=?flip@Rva0024C80DBitWords@@QAEXXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024C819 size=56 name=?friend_newModuleInstance@RefundDie@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *RefundDie::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new RefundDie(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C851 size=56 name=?friend_newModuleInstance@CreateCrateDie@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *CreateCrateDie::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new CreateCrateDie(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C889 size=56 name=?friend_newModuleInstance@CreateObjectDie@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024C8C1 size=81 name=?friend_newModuleData@CreateObjectDieModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *CreateObjectDieModuleData::friend_newModuleData(INI *ini)
{
	CreateObjectDieModuleData *data = new CreateObjectDieModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, CreateObjectDieModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024C912 size=56 name=?friend_newModuleInstance@CreateObjectDieIfEldestKindof@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *CreateObjectDieIfEldestKindof::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new CreateObjectDieIfEldestKindof(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C94A size=81 name=?friend_newModuleData@CreateObjectDieIfEldestKindofModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *CreateObjectDieIfEldestKindofModuleData::friend_newModuleData(INI *ini)
{
	CreateObjectDieIfEldestKindofModuleData *data = new CreateObjectDieIfEldestKindofModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, CreateObjectDieIfEldestKindofModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024C99B size=56 name=?friend_newModuleInstance@DamageFilteredCreateObjectDie@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *DamageFilteredCreateObjectDie::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new DamageFilteredCreateObjectDie(thing, moduleData);
}
// FUNCTION: BFME2 0x0024C9D3 size=81 name=?friend_newModuleData@DamageFilteredCreateObjectDieModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *DamageFilteredCreateObjectDieModuleData::friend_newModuleData(INI *ini)
{
	DamageFilteredCreateObjectDieModuleData *data = new DamageFilteredCreateObjectDieModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, DamageFilteredCreateObjectDieModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024CA38 size=56 name=?friend_newModuleInstance@CrushDie@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *CrushDie::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new CrushDie(thing, moduleData);
}
// FUNCTION: BFME2 0x0024CA70 size=56 name=?friend_newModuleInstance@DestroyDie@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *DestroyDie::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new DestroyDie(thing, moduleData);
}
// FUNCTION: BFME2 0x0024CAA8 size=56 name=?friend_newModuleInstance@FXListDie@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *FXListDie::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new FXListDie(thing, moduleData);
}
// FUNCTION: BFME2 0x0024CAE0 size=56 name=?friend_newModuleInstance@RebuildHoleExposeDie@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *RebuildHoleExposeDie::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new RebuildHoleExposeDie(thing, moduleData);
}
// FUNCTION: BFME2 0x0024CB18 size=81 name=?friend_newModuleData@RebuildHoleExposeDieModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *RebuildHoleExposeDieModuleData::friend_newModuleData(INI *ini)
{
	RebuildHoleExposeDieModuleData *data = new RebuildHoleExposeDieModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, RebuildHoleExposeDieModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024CB69 size=56 name=?friend_newModuleInstance@SpecialPowerCompletionDie@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *SpecialPowerCompletionDie::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new SpecialPowerCompletionDie(thing, moduleData);
}
// FUNCTION: BFME2 0x0024CBA1 size=56 name=?friend_newModuleInstance@UpgradeDie@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *UpgradeDie::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new UpgradeDie(thing, moduleData);
}
// FUNCTION: BFME2 0x0024CBD9 size=56 name=?friend_newModuleInstance@KeepObjectDie@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *KeepObjectDie::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new KeepObjectDie(thing, moduleData);
}
// FUNCTION: BFME2 0x0024CC11 size=56 name=?friend_newModuleInstance@AssistedTargetingUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *AssistedTargetingUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new AssistedTargetingUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024CC49 size=59 name=?friend_newModuleInstance@BoneFXUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024CC84 size=56 name=?friend_newModuleInstance@DefaultProductionExitUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *DefaultProductionExitUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new DefaultProductionExitUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024CCBC size=56 name=?friend_newModuleInstance@DelayedWeaponSetUpgradeUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *DelayedWeaponSetUpgradeUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new DelayedWeaponSetUpgradeUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024CCF4 size=81 name=?friend_newModuleData@DelayedWeaponSetUpgradeUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *DelayedWeaponSetUpgradeUpdateModuleData::friend_newModuleData(INI *ini)
{
	DelayedWeaponSetUpgradeUpdateModuleData *data = new DelayedWeaponSetUpgradeUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, DelayedWeaponSetUpgradeUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024CD45 size=56 name=?friend_newModuleInstance@DeletionUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *DeletionUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new DeletionUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024CD7D size=59 name=?friend_newModuleInstance@DozerAIUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *DozerAIUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new DozerAIUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024CDB8 size=81 name=?friend_newModuleData@DozerAIUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *DozerAIUpdateModuleData::friend_newModuleData(INI *ini)
{
	DozerAIUpdateModuleData *data = new DozerAIUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, DozerAIUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024CE09 size=59 name=?friend_newModuleInstance@DynamicShroudClearingRangeUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *DynamicShroudClearingRangeUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new DynamicShroudClearingRangeUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024CE44 size=81 name=?friend_newModuleData@DynamicShroudClearingRangeUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *DynamicShroudClearingRangeUpdateModuleData::friend_newModuleData(INI *ini)
{
	DynamicShroudClearingRangeUpdateModuleData *data = new DynamicShroudClearingRangeUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, DynamicShroudClearingRangeUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024CE95 size=56 name=?friend_newModuleInstance@FireSpreadUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *FireSpreadUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new FireSpreadUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024CECD size=81 name=?friend_newModuleData@FireSpreadUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *FireSpreadUpdateModuleData::friend_newModuleData(INI *ini)
{
	FireSpreadUpdateModuleData *data = new FireSpreadUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, FireSpreadUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024CF1E size=56 name=?friend_newModuleInstance@FireWeaponUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *FireWeaponUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new FireWeaponUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024CF56 size=81 name=?friend_newModuleData@FireWeaponUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *FireWeaponUpdateModuleData::friend_newModuleData(INI *ini)
{
	FireWeaponUpdateModuleData *data = new FireWeaponUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, FireWeaponUpdateModuleData::buildFieldParse);
	return data;
}

// FUNCTION: BFME2 0x0024CFA7 size=56 name=?friend_newModuleInstance@OilSpillUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *OilSpillUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new OilSpillUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024CFDF size=81 name=?friend_newModuleData@OilSpillUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *OilSpillUpdateModuleData::friend_newModuleData(INI *ini)
{
	OilSpillUpdateModuleData *data = new OilSpillUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, OilSpillUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024D030 size=56 name=?friend_newModuleInstance@FlammableUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *FlammableUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new FlammableUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024D068 size=81 name=?friend_newModuleData@FlammableUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *FlammableUpdateModuleData::friend_newModuleData(INI *ini)
{
	FlammableUpdateModuleData *data = new FlammableUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, FlammableUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024D0B9 size=56 name=?friend_newModuleInstance@FloatUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *FloatUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new FloatUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024D0F1 size=81 name=?friend_newModuleData@FloatUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *FloatUpdateModuleData::friend_newModuleData(INI *ini)
{
	FloatUpdateModuleData *data = new FloatUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, FloatUpdateModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024D142 size=56 name=?friend_newModuleInstance@FloodUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024D17A size=81 name=?friend_newModuleData@FloodUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *FloodUpdateModuleData::friend_newModuleData(INI *ini)
{
	FloodUpdateModuleData *data = new FloodUpdateModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, FloodUpdateModuleData::buildFieldParse);
	return data;
}

// Field parse table for DeployStyleAIUpdateModuleData (decoded from retail image).
static const FieldParse s_deployStyleAIUpdateModuleDataFieldParse[] =
{
	{ "UnpackTime", INI::parseDurationUnsignedInt, 0, 0x64 },
	{ "PackTime", INI::parseDurationUnsignedInt, 0, 0x68 },
	{ "ResetTurretBeforePacking", INI::parseBool, 0, 0x6C },
	{ "TurretsFunctionOnlyWhenDeployed", INI::parseBool, 0, 0x6D },
	{ "TurretsMustCenterBeforePacking", INI::parseBool, 0, 0x6E },
	{ "MustDeployToAttack", INI::parseBool, 0, 0x6F },
	{ "DeployedAttributeModifier", INI::parseAsciiString, 0, 0x70 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x0024D1CB size=27 name=?buildFieldParse@DeployStyleAIUpdateModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void DeployStyleAIUpdateModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	AIUpdateModuleData::buildFieldParse(parse);
	parse.add(s_deployStyleAIUpdateModuleDataFieldParse, 0);
}

// FUNCTION: BFME2 0x0024D1E6 size=59 name=?friend_newModuleInstance@DeployStyleAIUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *DeployStyleAIUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new DeployStyleAIUpdate(thing, moduleData);
}
