// Configures when units replenish and the effects to play.
#pragma once
#ifndef BFME2_REPLENISH_UNITS_BEHAVIOR_MODULE_DATA_H
#define BFME2_REPLENISH_UNITS_BEHAVIOR_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/ModuleData.h"
#include "GameLogic/Module/UpgradeMuxData.h"
#include "Common/BitFlags.h"

class INI;
class MultiIniFieldParse;
class FXList;

class ReplenishUnitsBehaviorModuleData : public ModuleData
{
public:
	ReplenishUnitsBehaviorModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);

	UpgradeMuxData m_upgradeMuxData;                       // +0x8; added by buildFieldParse at +0x8
	Real m_replenishRadius;                                // +0x118 ReplenishRadius
	Real m_noReplenishIfEnemyWithinRadius;                 // +0x11C NoReplenishIfEnemyWithinRadius
	const FXList * m_replenishFXList;                      // +0x120 ReplenishFXList
	ObjectStatusMaskType m_replenishStatii;                // +0x124 ReplenishStatii; BitFlags<101>
	UnsignedInt m_replenishDelay;                          // +0x134 ReplenishDelay; duration, frames
	Bool m_startsActive;                                   // +0x138 StartsActive
	Bool m_replenishHordeMembersOnly;                      // +0x139 ReplenishHordeMembersOnly
};
// SIZE 0x13C
typedef char ReplenishUnitsBehaviorModuleData_size[(sizeof(ReplenishUnitsBehaviorModuleData) == 0x13C) ? 1 : -1];
typedef char ReplenishUnitsBehaviorModuleData_off_m_upgradeMuxData[(offsetof(ReplenishUnitsBehaviorModuleData, m_upgradeMuxData) == 0x8) ? 1 : -1];
typedef char ReplenishUnitsBehaviorModuleData_off_m_replenishRadius[(offsetof(ReplenishUnitsBehaviorModuleData, m_replenishRadius) == 0x118) ? 1 : -1];
typedef char ReplenishUnitsBehaviorModuleData_off_m_noReplenishIfEnemyWithinRadius[(offsetof(ReplenishUnitsBehaviorModuleData, m_noReplenishIfEnemyWithinRadius) == 0x11C) ? 1 : -1];
typedef char ReplenishUnitsBehaviorModuleData_off_m_replenishFXList[(offsetof(ReplenishUnitsBehaviorModuleData, m_replenishFXList) == 0x120) ? 1 : -1];
typedef char ReplenishUnitsBehaviorModuleData_off_m_replenishStatii[(offsetof(ReplenishUnitsBehaviorModuleData, m_replenishStatii) == 0x124) ? 1 : -1];
typedef char ReplenishUnitsBehaviorModuleData_off_m_replenishDelay[(offsetof(ReplenishUnitsBehaviorModuleData, m_replenishDelay) == 0x134) ? 1 : -1];
typedef char ReplenishUnitsBehaviorModuleData_off_m_startsActive[(offsetof(ReplenishUnitsBehaviorModuleData, m_startsActive) == 0x138) ? 1 : -1];
typedef char ReplenishUnitsBehaviorModuleData_off_m_replenishHordeMembersOnly[(offsetof(ReplenishUnitsBehaviorModuleData, m_replenishHordeMembersOnly) == 0x139) ? 1 : -1];

#endif
