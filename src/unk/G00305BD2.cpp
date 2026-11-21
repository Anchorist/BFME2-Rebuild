// cl: /O1
#include "Common/Xfer.h"
// Save-game transfer helpers for enumerated values. Each hands an int-sized enum to Xfer::XferEnum with the name of
// its enum type (the string retail stores, used to tag the value in the save) and its size in bytes.
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G00305BD2 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x00305BD2 size=24 name=?XferModelConditionFlagType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferModelConditionFlagType(Xfer *xfer, int *value)
{
	xfer->XferEnum("ModelConditionFlagType", value, 4);
}
// FUNCTION: BFME2 0x00305BEA size=24 name=?XferGameDifficulty@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferGameDifficulty(Xfer *xfer, int *value)
{
	xfer->XferEnum("GameDifficulty", value, 4);
}
// FUNCTION: BFME2 0x00305C02 size=24 name=?XferCommandSourceType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferCommandSourceType(Xfer *xfer, int *value)
{
	xfer->XferEnum("CommandSourceType", value, 4);
}
// FUNCTION: BFME2 0x00305C1A size=24 name=?XferWhichTurretType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferWhichTurretType(Xfer *xfer, int *value)
{
	xfer->XferEnum("WhichTurretType", value, 4);
}
// FUNCTION: BFME2 0x00305C32 size=24 name=?XferRelationship@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferRelationship(Xfer *xfer, int *value)
{
	xfer->XferEnum("Relationship", value, 4);
}
// FUNCTION: BFME2 0x00305C4A size=24 name=?XferFormationID@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferFormationID(Xfer *xfer, int *value)
{
	xfer->XferEnum("FormationID", value, 4);
}
// FUNCTION: BFME2 0x00305C62 size=24 name=?XferWaypointID@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferWaypointID(Xfer *xfer, int *value)
{
	xfer->XferEnum("WaypointID", value, 4);
}
// FUNCTION: BFME2 0x00305C7A size=24 name=?XferTimeOfDay@@YAXPAVXfer@@PAX@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferTimeOfDay(Xfer *xfer, void *value)
{
	xfer->XferEnum("TimeOfDay", value, 4);
}
// FUNCTION: BFME2 0x00305C92 size=24 name=?XferWeather@@YAXPAVXfer@@PAX@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferWeather(Xfer *xfer, void *value)
{
	xfer->XferEnum("Weather", value, 4);
}
// FUNCTION: BFME2 0x00305CAA size=24 name=?XferFactionType@@YAXPAVXfer@@PAX@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferFactionType(Xfer *xfer, void *value)
{
	xfer->XferEnum("FactionType", value, 4);
}
// FUNCTION: BFME2 0x00305CC2 size=24 name=?XferLivingWorldObjectType@@YAXPAVXfer@@PAX@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferLivingWorldObjectType(Xfer *xfer, void *value)
{
	xfer->XferEnum("LivingWorldObjectType", value, 4);
}
// FUNCTION: BFME2 0x00305CDA size=24 name=?XferScorches@@YAXPAVXfer@@PAX@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferScorches(Xfer *xfer, void *value)
{
	xfer->XferEnum("Scorches", value, 4);
}
// FUNCTION: BFME2 0x00305CF2 size=24 name=?XferWeaponSlotType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferWeaponSlotType(Xfer *xfer, int *value)
{
	xfer->XferEnum("WeaponSlotType", value, 4);
}
// FUNCTION: BFME2 0x00305D0A size=24 name=?XferPathfindLayerEnum@@YAPAVXfer@@PAV1@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Xfer *XferPathfindLayerEnum(Xfer *xfer, int *value)
{
	return &xfer->XferEnum("PathfindLayerEnum", value, 4);
}
// FUNCTION: BFME2 0x00305D22 size=24 name=?XferOrderMode@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferOrderMode(Xfer *xfer, int *value)
{
	xfer->XferEnum("OrderMode", value, 4);
}
// FUNCTION: BFME2 0x00305D3A size=24 name=?XferRadarEventType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferRadarEventType(Xfer *xfer, int *value)
{
	xfer->XferEnum("RadarEventType", value, 4);
}
// FUNCTION: BFME2 0x00305D52 size=24 name=?XferSaveFileType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferSaveFileType(Xfer *xfer, int *value)
{
	xfer->XferEnum("SaveFileType", value, 4);
}
// FUNCTION: BFME2 0x00305D6A size=24 name=?XferBuildableStatus@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferBuildableStatus(Xfer *xfer, int *value)
{
	xfer->XferEnum("BuildableStatus", value, 4);
}
// FUNCTION: BFME2 0x00305D82 size=24 name=?XferWeaponStatus@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferWeaponStatus(Xfer *xfer, int *value)
{
	xfer->XferEnum("WeaponStatus", value, 4);
}
// FUNCTION: BFME2 0x00305D9A size=24 name=?XferAttitudeType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferAttitudeType(Xfer *xfer, int *value)
{
	xfer->XferEnum("AttitudeType", value, 4);
}
// FUNCTION: BFME2 0x00305DB2 size=24 name=?XferAICommandType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferAICommandType(Xfer *xfer, int *value)
{
	xfer->XferEnum("AICommandType", value, 4);
}
// FUNCTION: BFME2 0x00305DCA size=24 name=?XferTurretTargetType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferTurretTargetType(Xfer *xfer, int *value)
{
	xfer->XferEnum("TurretTargetType", value, 4);
}
// FUNCTION: BFME2 0x00305DE2 size=24 name=?XferAimWeaponBehaviorAimType@@YAXPAVXfer@@PAX@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferAimWeaponBehaviorAimType(Xfer *xfer, void *value)
{
	xfer->XferEnum("AimWeaponBehavior::AimType", value, 4);
}
// FUNCTION: BFME2 0x00305DFA size=24 name=?XferScaffoldTargetMotion@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferScaffoldTargetMotion(Xfer *xfer, int *value)
{
	xfer->XferEnum("ScaffoldTargetMotion", value, 4);
}
// FUNCTION: BFME2 0x00305E12 size=24 name=?XferBodyDamageType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferBodyDamageType(Xfer *xfer, int *value)
{
	xfer->XferEnum("BodyDamageType", value, 4);
}
// FUNCTION: BFME2 0x00305E2A size=24 name=?XferBodySideDestroyedType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferBodySideDestroyedType(Xfer *xfer, int *value)
{
	xfer->XferEnum("BodySideDestroyedType", value, 4);
}
// FUNCTION: BFME2 0x00305E42 size=24 name=?XferLocomotorSetType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferLocomotorSetType(Xfer *xfer, int *value)
{
	xfer->XferEnum("LocomotorSetType", value, 4);
}
// FUNCTION: BFME2 0x00305E5A size=24 name=?XferGuardTargetType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferGuardTargetType(Xfer *xfer, int *value)
{
	xfer->XferEnum("GuardTargetType", value, 4);
}
// FUNCTION: BFME2 0x00305E72 size=24 name=?XferFlammabilityStatusType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferFlammabilityStatusType(Xfer *xfer, int *value)
{
	xfer->XferEnum("FlammabilityStatusType", value, 4);
}
// FUNCTION: BFME2 0x00305E8A size=24 name=?XferDeployStateTypes@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferDeployStateTypes(Xfer *xfer, int *value)
{
	xfer->XferEnum("DeployStateTypes", value, 4);
}
// FUNCTION: BFME2 0x00305EA2 size=24 name=?XferCommandResultTypes@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferCommandResultTypes(Xfer *xfer, int *value)
{
	xfer->XferEnum("DeployStyleAIUpdate::CommandResultTypes", value, 4);
}
// FUNCTION: BFME2 0x00305EBA size=24 name=?XferDamageFXType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferDamageFXType(Xfer *xfer, int *value)
{
	xfer->XferEnum("DamageFXType", value, 4);
}
// FUNCTION: BFME2 0x00305ED2 size=24 name=?XferDamageType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferDamageType(Xfer *xfer, int *value)
{
	xfer->XferEnum("DamageType", value, 4);
}
// FUNCTION: BFME2 0x00305EEA size=24 name=?XferDamageSubType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferDamageSubType(Xfer *xfer, int *value)
{
	xfer->XferEnum("DamageSubType", value, 4);
}
// FUNCTION: BFME2 0x00305F02 size=24 name=?XferDeathType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferDeathType(Xfer *xfer, int *value)
{
	xfer->XferEnum("DeathType", value, 4);
}
// FUNCTION: BFME2 0x00305F1A size=24 name=?XferStealthLookType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferStealthLookType(Xfer *xfer, int *value)
{
	xfer->XferEnum("StealthLookType", value, 4);
}
// FUNCTION: BFME2 0x00305F32 size=24 name=?XferFXAction@@YAXPAVXfer@@PAX@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferFXAction(Xfer *xfer, void *value)
{
	xfer->XferEnum("FXAction", value, 4);
}
// FUNCTION: BFME2 0x00305F4A size=24 name=?XferFXTrigger@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferFXTrigger(Xfer *xfer, int *value)
{
	xfer->XferEnum("FXTrigger", value, 4);
}
// FUNCTION: BFME2 0x00305F62 size=24 name=?XferFX_Types@@YAXPAVXfer@@PAX@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferFX_Types(Xfer *xfer, void *value)
{
	xfer->XferEnum("FX_Types", value, 4);
}
// FUNCTION: BFME2 0x00305F7A size=24 name=?XferShadowType@@YAXPAVXfer@@PAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void XferShadowType(Xfer *xfer, int *value)
{
	xfer->XferEnum("ShadowType", value, 4);
}
