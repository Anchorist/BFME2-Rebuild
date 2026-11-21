#include "Common/INI.h"
#include "GameLogic/Module/SiegeDeploySpecialPowerModuleData.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004C55B2 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x004C55B2 size=74 name=?onCollide@DeflectSpecialPower@@UAEXPAVObject@@PBVCoord3D@@1@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x004C55FC size=117 name=?update@DeflectSpecialPower@@UAE?AW4UpdateSleepTime@@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x004C569F size=27 name=?buildFieldParse@SiegeDeploySpecialPowerModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void SiegeDeploySpecialPowerModuleData::buildFieldParse(MultiIniFieldParse &p)
{
	SpecialPowerUpdateModuleData::buildFieldParse(p);
	static const FieldParse dataFieldParse[] = {
		{ "LowerDelay", INI::parseDurationUnsignedInt, 0, 0x18 },
		{ "RaiseDelay", INI::parseDurationUnsignedInt, 0, 0x1C },
		{ "EvacuatePassengersOnDeploy", INI::parseBool, 0, 0x20 },
		{ "EvacuateCrewOnDeploy", INI::parseBool, 0, 0x21 },
		{ "SkipAdjustPosition", INI::parseBool, 0, 0x22 },
		{ "WallSearchDistance", INI::parseReal, 0, 0x24 },
		{ "AwayFromWallWaitDist", INI::parseReal, 0, 0x28 },
		{ "ExtraWallDistance", INI::parseReal, 0, 0x2C },
		{ 0, 0, 0, 0 }
	};
	p.add(dataFieldParse);
}
// FUNCTION: BFME2 0x004C56BA size=124 name=??0SiegeDeploySpecialPower@@QAE@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
