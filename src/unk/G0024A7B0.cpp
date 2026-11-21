// cl: /O1
// stlport46
#include "Common/INI.h"
#include "GameLogic/Module/CaveContainModuleData.h"
#include "GameLogic/Module/OpenContainModuleData.h"
#include "GameLogic/Module/TunnelContainModuleData.h"
#include "GameLogic/Module/HordeGarrisonContainModuleData.h"
#include "GameLogic/Module/HitReactionBehavior.h"
#include "GameLogic/Module/RampageBehaviorModuleData.h"
#include "GameLogic/Module/RampageBehavior.h"
#include "GameLogic/Module/BridgeTowerBehavior.h"
#include "GameLogic/Module/BridgeBehaviorModuleData.h"
#include "GameLogic/Module/BuildingBehaviorModuleData.h"
#include "GameLogic/Module/BuildingBehavior.h"
#include "GameLogic/Module/CastleMemberBehaviorModuleData.h"
#include "GameLogic/Module/CastleBehaviorModuleData.h"
#include "GameLogic/Module/FoundationAIUpdate.h"
#include "GameLogic/Module/GettingBuiltBehaviorModuleData.h"
#include "GameLogic/Module/AutoHealBehavior.h"
#include "GameLogic/Module/ShipSlowDeathBehaviorModuleData.h"
#include "GameLogic/Module/ShipSlowDeathBehavior.h"
#include "GameLogic/Module/SlowDeathBehaviorModuleData.h"
#include "GameLogic/Module/SlowDeathBehavior.h"
#include "GameLogic/Module/InstantDeathBehavior.h"
#include "GameLogic/Module/AimWeaponBehaviorModuleData.h"
#include "GameLogic/Module/DualWeaponBehaviorModuleData.h"
#include "GameLogic/Module/AutoAbilityBehavior.h"
#include "GameLogic/Module/ClickReactionBehaviorModuleData.h"
#include "GameLogic/Module/HitReactionBehaviorModuleData.h"
#include "GameLogic/Module/CaveContain.h"
#include "GameLogic/Module/GarrisonContain.h"
#include "GameLogic/Module/HordeTransportContainModuleData.h"
#include "GameLogic/Module/HordeTransportContain.h"
#include "GameLogic/Module/HorseHordeContain.h"
#include "GameLogic/Module/HordeContain.h"
#include "GameLogic/Module/TransportContainModuleData.h"
#include "GameLogic/Module/TransportContain.h"
#include "GameLogic/Module/HealContainModuleData.h"
#include "GameLogic/Module/HealContain.h"
#include "GameLogic/Module/OpenContain.h"
#include "GameLogic/Module/RunOffMapBehavior.h"
#include "GameLogic/Module/MineshaftPortalBehaviourModuleData.h"
#include "GameLogic/Module/GiantBirdSlowDeathBehaviorModuleData.h"
#include "GameLogic/Module/GiantBirdSlowDeathBehavior.h"
#include "GameLogic/Module/FakePathfindPortalBehaviour.h"
#include "GameLogic/Module/DynamicPortalBehaviour.h"
#include "GameLogic/Module/WargBehavior.h"
#include "GameLogic/Module/SpawnBehavior.h"
#include "GameLogic/Module/StancesBehavior.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G0024A7B0 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x0024A7B0 size=56 name=?friend_newModuleInstance@BloodthirstyUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024A7E8 size=81 name=?friend_newModuleData@BloodthirstyUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024A847 size=59 name=?friend_newModuleInstance@SpecialAbilityUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024A882 size=84 name=?friend_newModuleData@SpecialAbilityUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024A8D6 size=6 name=?Rva0024A8D6Get@@YAHXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// Returns a fixed constant (a flag mask or size); its role in the original is not recovered, so the ledger name stays.
int Rva0024A8D6Get()
{
	return 132;
}
// FUNCTION: BFME2 0x0024A8DC size=56 name=?friend_newModuleInstance@AutoHealBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *AutoHealBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new AutoHealBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024A914 size=56 name=?friend_newModuleInstance@WallHubBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024A94C size=81 name=?friend_newModuleData@WallHubBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024A99D size=56 name=?friend_newModuleInstance@GettingBuiltBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024A9D5 size=81 name=?friend_newModuleData@GettingBuiltBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *GettingBuiltBehaviorModuleData::friend_newModuleData(INI *ini)
{
	GettingBuiltBehaviorModuleData *data = new GettingBuiltBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, GettingBuiltBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024AA26 size=56 name=?friend_newModuleInstance@FoundationAIUpdate@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *FoundationAIUpdate::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new FoundationAIUpdate(thing, moduleData);
}
// FUNCTION: BFME2 0x0024AA5E size=59 name=?friend_newModuleInstance@CastleBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024AA99 size=81 name=?friend_newModuleData@CastleBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *CastleBehaviorModuleData::friend_newModuleData(INI *ini)
{
	CastleBehaviorModuleData *data = new CastleBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, CastleBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024AAEA size=4 name=?get@Rva0024AAEAConst@@SAHXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024AAEE size=56 name=?friend_newModuleInstance@CastleMemberBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024AB26 size=81 name=?friend_newModuleData@CastleMemberBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *CastleMemberBehaviorModuleData::friend_newModuleData(INI *ini)
{
	CastleMemberBehaviorModuleData *data = new CastleMemberBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, CastleMemberBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024AB77 size=56 name=?friend_newModuleInstance@BuildingBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *BuildingBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new BuildingBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024ABAF size=81 name=?friend_newModuleData@BuildingBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *BuildingBehaviorModuleData::friend_newModuleData(INI *ini)
{
	BuildingBehaviorModuleData *data = new BuildingBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, BuildingBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024AC00 size=59 name=?friend_newModuleInstance@BridgeBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024AC3B size=81 name=?friend_newModuleData@BridgeBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *BridgeBehaviorModuleData::friend_newModuleData(INI *ini)
{
	BridgeBehaviorModuleData *data = new BridgeBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, BridgeBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024AC8C size=4 name=?get@Rva0024AC8CConst@@SAHXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024AC90 size=56 name=?friend_newModuleInstance@BridgeScaffoldBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024ACC8 size=56 name=?friend_newModuleInstance@BridgeTowerBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *BridgeTowerBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new BridgeTowerBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024AD00 size=56 name=?friend_newModuleInstance@RampageBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *RampageBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new RampageBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024AD38 size=81 name=?friend_newModuleData@RampageBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *RampageBehaviorModuleData::friend_newModuleData(INI *ini)
{
	RampageBehaviorModuleData *data = new RampageBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, RampageBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024AD89 size=56 name=?friend_newModuleInstance@EnragedBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024ADC1 size=81 name=?friend_newModuleData@EnragedBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024AE12 size=56 name=?friend_newModuleInstance@HitReactionBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *HitReactionBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new HitReactionBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024AE4A size=81 name=?friend_newModuleData@HitReactionBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *HitReactionBehaviorModuleData::friend_newModuleData(INI *ini)
{
	HitReactionBehaviorModuleData *data = new HitReactionBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, HitReactionBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024AE9B size=56 name=?friend_newModuleInstance@ClickReactionBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024AED3 size=81 name=?friend_newModuleData@ClickReactionBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *ClickReactionBehaviorModuleData::friend_newModuleData(INI *ini)
{
	ClickReactionBehaviorModuleData *data = new ClickReactionBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, ClickReactionBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024AF24 size=56 name=?friend_newModuleInstance@SiegeDockingBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024AF5C size=81 name=?friend_newModuleData@SiegeDockingBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024AFAD size=56 name=?friend_newModuleInstance@AutoAbilityBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *AutoAbilityBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new AutoAbilityBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024AFE5 size=81 name=?friend_newModuleData@AutoAbilityBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024B036 size=56 name=?friend_newModuleInstance@DualWeaponBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024B06E size=81 name=?friend_newModuleData@DualWeaponBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *DualWeaponBehaviorModuleData::friend_newModuleData(INI *ini)
{
	DualWeaponBehaviorModuleData *data = new DualWeaponBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, DualWeaponBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024B0BF size=56 name=?friend_newModuleInstance@AimWeaponBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024B0F7 size=81 name=?friend_newModuleData@AimWeaponBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *AimWeaponBehaviorModuleData::friend_newModuleData(INI *ini)
{
	AimWeaponBehaviorModuleData *data = new AimWeaponBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, AimWeaponBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024B148 size=59 name=?friend_newModuleInstance@BezierProjectileBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024B183 size=84 name=?friend_newModuleData@BezierProjectileBehavior@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024B1D7 size=4 name=?get@Rva0024B1D7Const@@SAHXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024B1DB size=56 name=?friend_newModuleInstance@InstantDeathBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *InstantDeathBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new InstantDeathBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024B213 size=81 name=?friend_newModuleData@InstantDeathBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024B264 size=56 name=?friend_newModuleInstance@SlowDeathBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *SlowDeathBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new SlowDeathBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024B29C size=84 name=?friend_newModuleData@SlowDeathBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *SlowDeathBehaviorModuleData::friend_newModuleData(INI *ini)
{
	SlowDeathBehaviorModuleData *data = new SlowDeathBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, SlowDeathBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024B2F0 size=56 name=?friend_newModuleInstance@ShipSlowDeathBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *ShipSlowDeathBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new ShipSlowDeathBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024B328 size=84 name=?friend_newModuleData@ShipSlowDeathBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *ShipSlowDeathBehaviorModuleData::friend_newModuleData(INI *ini)
{
	ShipSlowDeathBehaviorModuleData *data = new ShipSlowDeathBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, ShipSlowDeathBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024B37C size=56 name=?friend_newModuleInstance@StancesBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *StancesBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new StancesBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024B3B4 size=81 name=?friend_newModuleData@StancesBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024B405 size=56 name=?friend_newModuleInstance@SpawnBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *SpawnBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new SpawnBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024B43D size=6 name=?Rva0024B43DGet@@YAHXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// Returns a fixed constant (a flag mask or size); its role in the original is not recovered, so the ledger name stays.
int Rva0024B43DGet()
{
	return 135;
}
// FUNCTION: BFME2 0x0024B443 size=56 name=?friend_newModuleInstance@WargBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *WargBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new WargBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024B47B size=56 name=?friend_newModuleInstance@DynamicPortalBehaviour@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *DynamicPortalBehaviour::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new DynamicPortalBehaviour(thing, moduleData);
}
// FUNCTION: BFME2 0x0024B4B3 size=84 name=?friend_newModuleData@DynamicPortalBehaviourModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024B507 size=6 name=?Rva0024B507Get@@YAHXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// Returns a fixed constant (a flag mask or size); its role in the original is not recovered, so the ledger name stays.
int Rva0024B507Get()
{
	return 142;
}
// FUNCTION: BFME2 0x0024B50D size=56 name=?friend_newModuleInstance@FakePathfindPortalBehaviour@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *FakePathfindPortalBehaviour::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new FakePathfindPortalBehaviour(thing, moduleData);
}
// FUNCTION: BFME2 0x0024B545 size=84 name=?friend_newModuleData@FakePathfindPortalBehaviourModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024B599 size=56 name=?friend_newModuleInstance@GiantBirdSlowDeathBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *GiantBirdSlowDeathBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new GiantBirdSlowDeathBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024B5D1 size=84 name=?friend_newModuleData@GiantBirdSlowDeathBehaviorModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *GiantBirdSlowDeathBehaviorModuleData::friend_newModuleData(INI *ini)
{
	GiantBirdSlowDeathBehaviorModuleData *data = new GiantBirdSlowDeathBehaviorModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, GiantBirdSlowDeathBehaviorModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024B625 size=56 name=?friend_newModuleInstance@MineshaftPortalBehaviour@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024B65D size=84 name=?friend_newModuleData@MineshaftPortalBehaviourModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *MineshaftPortalBehaviourModuleData::friend_newModuleData(INI *ini)
{
	MineshaftPortalBehaviourModuleData *data = new MineshaftPortalBehaviourModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, MineshaftPortalBehaviourModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024B6B1 size=56 name=?friend_newModuleInstance@RunOffMapBehavior@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *RunOffMapBehavior::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new RunOffMapBehavior(thing, moduleData);
}
// FUNCTION: BFME2 0x0024B6E9 size=59 name=?friend_newModuleInstance@OpenContain@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *OpenContain::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new OpenContain(thing, moduleData);
}
// FUNCTION: BFME2 0x0024B724 size=84 name=?friend_newModuleData@OpenContain@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024B778 size=4 name=?get@Rva0024B778Const@@SAHXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// Field parse table for CaveContainModuleData (decoded from retail image).
static const FieldParse s_caveContainModuleDataFieldParse[] =
{
	{ "CaveIndex", INI::parseInt, 0, 0x98 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x0024B77C size=27 name=?buildFieldParse@CaveContainModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void CaveContainModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	OpenContainModuleData::buildFieldParse(parse);
	parse.add(s_caveContainModuleDataFieldParse, 0);
}

// FUNCTION: BFME2 0x0024B797 size=59 name=?friend_newModuleInstance@CaveContain@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *CaveContain::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new CaveContain(thing, moduleData);
}
// FUNCTION: BFME2 0x0024B7D2 size=59 name=?friend_newModuleInstance@HealContain@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *HealContain::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new HealContain(thing, moduleData);
}
// FUNCTION: BFME2 0x0024B80D size=84 name=?friend_newModuleData@HealContainModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *HealContainModuleData::friend_newModuleData(INI *ini)
{
	HealContainModuleData *data = new HealContainModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, HealContainModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024B861 size=59 name=?friend_newModuleInstance@TransportContain@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *TransportContain::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new TransportContain(thing, moduleData);
}
// FUNCTION: BFME2 0x0024B89C size=84 name=?friend_newModuleData@TransportContainModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *TransportContainModuleData::friend_newModuleData(INI *ini)
{
	TransportContainModuleData *data = new TransportContainModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, TransportContainModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024B8F0 size=59 name=?friend_newModuleInstance@HordeContain@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *HordeContain::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new HordeContain(thing, moduleData);
}
// FUNCTION: BFME2 0x0024B92B size=84 name=?friend_newModuleData@HordeContainModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024B97F size=59 name=?friend_newModuleInstance@HorseHordeContain@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *HorseHordeContain::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new HorseHordeContain(thing, moduleData);
}
// FUNCTION: BFME2 0x0024B9CC size=59 name=?friend_newModuleInstance@HordeTransportContain@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *HordeTransportContain::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new HordeTransportContain(thing, moduleData);
}
// FUNCTION: BFME2 0x0024BA07 size=84 name=?friend_newModuleData@HordeTransportContainModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *HordeTransportContainModuleData::friend_newModuleData(INI *ini)
{
	HordeTransportContainModuleData *data = new HordeTransportContainModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, HordeTransportContainModuleData::buildFieldParse);
	return data;
}
// FUNCTION: BFME2 0x0024BA5B size=59 name=?friend_newModuleInstance@GarrisonContain@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Module *GarrisonContain::friend_newModuleInstance(Thing *thing, const ModuleData *moduleData)
{
	return new GarrisonContain(thing, moduleData);
}
// FUNCTION: BFME2 0x0024BA96 size=59 name=?friend_newModuleInstance@HordeGarrisonContain@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024BAD1 size=84 name=?friend_newModuleData@HordeGarrisonContainModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024BB25 size=59 name=?friend_newModuleInstance@AODHordeContain@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024BB60 size=84 name=?friend_newModuleData@AODHordeContainModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024BBB4 size=59 name=?friend_newModuleInstance@SiegeEngineContain@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024BBEF size=84 name=?friend_newModuleData@SiegeEngineContainModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024BC43 size=59 name=?friend_newModuleInstance@HordeSiegeEngineContain@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024BC7E size=84 name=?friend_newModuleData@HordeSiegeEngineContainModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// Field parse table for TunnelContainModuleData (decoded from retail image).
static const FieldParse s_tunnelContainModuleDataFieldParse[] =
{
	{ "TimeForFullHeal", INI::parseDurationReal, 0, 0xD4 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x0024BCD2 size=27 name=?buildFieldParse@TunnelContainModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void TunnelContainModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	HordeGarrisonContainModuleData::buildFieldParse(parse);
	parse.add(s_tunnelContainModuleDataFieldParse, 0);
}

// FUNCTION: BFME2 0x0024BCED size=59 name=?friend_newModuleInstance@TunnelContain@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024BD28 size=59 name=?friend_newModuleInstance@RiderChangeContain@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024BD63 size=84 name=?friend_newModuleData@RiderChangeContainModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024BDB7 size=59 name=?friend_newModuleInstance@AIUpdateInterface@@SAPAVModule@@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0024BDF2 size=81 name=?friend_newModuleData@TransportAIUpdateModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
