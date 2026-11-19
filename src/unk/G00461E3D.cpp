// cl: /O1
#include <stddef.h>
#include "Common/INI.h"
#include "GameLogic/Module/GiantBirdSlowDeathBehaviorModuleData.h"

// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G00461E3D name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.

static const FieldParse s_giantBirdSlowDeathBehaviorFields[] =
{
	{ "FXHitGround", INI::parseFXList, 0, offsetof(GiantBirdSlowDeathBehaviorModuleData, m_fxHitGround) },
	{ "OCLHitGround", INI::parseObjectCreationList, 0, offsetof(GiantBirdSlowDeathBehaviorModuleData, m_oclHitGround) },
	{ "DelayFromGroundToFinalDeath", INI::parseDurationReal, 0, offsetof(GiantBirdSlowDeathBehaviorModuleData, m_delayFromGroundToFinalDeath) },
	{ "CrashAvoidKindOfs", KindOfMaskType::parseFromINI, 0, offsetof(GiantBirdSlowDeathBehaviorModuleData, m_crashAvoidKindOfs) },
	{ "CrashAvoidRadius", INI::parseReal, 0, offsetof(GiantBirdSlowDeathBehaviorModuleData, m_crashAvoidRadius) },
	{ "CrashAvoidStrength", INI::parseReal, 0, offsetof(GiantBirdSlowDeathBehaviorModuleData, m_crashAvoidStrength) },
	{ "NeedToMaintainFlailingHeight", INI::parseBool, 0, offsetof(GiantBirdSlowDeathBehaviorModuleData, m_needToMaintainFlailingHeight) },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x00461E3D size=27 name=?buildFieldParse@GiantBirdSlowDeathBehaviorModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void GiantBirdSlowDeathBehaviorModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	SlowDeathBehaviorModuleData::buildFieldParse(parse);
	parse.add(s_giantBirdSlowDeathBehaviorFields, 0);
}
