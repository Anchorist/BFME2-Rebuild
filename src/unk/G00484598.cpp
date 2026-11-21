// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G00484598 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include <stddef.h>
#include "GameLogic/Module/SlaveWatcherBehaviorModuleData.h"
#include "GameLogic/Module/ReplenishUnitsBehaviorModuleData.h"
#include "GameLogic/Module/UpgradeMuxData.h"
static const FieldParse s_replenishUnitsBehaviorModuleDataFieldParse[] =
{
	{ "StartsActive", INI::parseBool, 0, offsetof(ReplenishUnitsBehaviorModuleData, m_startsActive) },
	{ "ReplenishDelay", INI::parseDurationUnsignedInt, 0, offsetof(ReplenishUnitsBehaviorModuleData, m_replenishDelay) },
	{ "ReplenishRadius", INI::parseReal, 0, offsetof(ReplenishUnitsBehaviorModuleData, m_replenishRadius) },
	{ "NoReplenishIfEnemyWithinRadius", INI::parseReal, 0, offsetof(ReplenishUnitsBehaviorModuleData, m_noReplenishIfEnemyWithinRadius) },
	{ "ReplenishFXList", INI::parseFXList, 0, offsetof(ReplenishUnitsBehaviorModuleData, m_replenishFXList) },
	{ "ReplenishStatii", ObjectStatusMaskType::parseFromINI, 0, offsetof(ReplenishUnitsBehaviorModuleData, m_replenishStatii) },
	{ "ReplenishHordeMembersOnly", INI::parseBool, 0, offsetof(ReplenishUnitsBehaviorModuleData, m_replenishHordeMembersOnly) },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x00484598 size=34 name=?buildFieldParse@ReplenishUnitsBehaviorModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void ReplenishUnitsBehaviorModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_replenishUnitsBehaviorModuleDataFieldParse, 0);
	parse.add(UpgradeMuxData::getFieldParse(), offsetof(ReplenishUnitsBehaviorModuleData, m_upgradeMuxData));
}

static const FieldParse s_slaveWatcherBehaviorModuleDataFieldParse[] =
{
	{ "RemoveUpgrade", INI::parseAsciiString, 0, 0xC },
	{ "GrantUpgrade", INI::parseAsciiString, 0, 0x8 },
	{ "ShareUpgrades", INI::parseBool, 0, 0x10 },
	{ "LetSlaveLive", INI::parseBool, 0, 0x11 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004845BA size=17 name=?buildFieldParse@SlaveWatcherBehaviorModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void SlaveWatcherBehaviorModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_slaveWatcherBehaviorModuleDataFieldParse, 0);
}

