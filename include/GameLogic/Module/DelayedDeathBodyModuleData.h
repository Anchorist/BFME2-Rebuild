// Timing, prerequisite upgrade and effects for delayed death.
#pragma once
#ifndef BFME2_DELAYED_DEATH_BODY_MODULE_DATA_H
#define BFME2_DELAYED_DEATH_BODY_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/RespawnBodyModuleData.h"

class INI;
class MultiIniFieldParse;
class FXList;
class UpgradeTemplate;

// Base RespawnBodyModuleData: the constructor calls its constructor on this. It ends at 0x6C (its own operator-new size);
// this class's members follow it.
typedef char DelayedDeathBodyModuleData_base_size[(sizeof(RespawnBodyModuleData) == 0x6C) ? 1 : -1];

class DelayedDeathBodyModuleData : public RespawnBodyModuleData
{
public:
	DelayedDeathBodyModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);

	UnsignedInt m_delayedDeathTime;                        // +0x6C DelayedDeathTime; duration, frames
	Bool m_immortalUntilDeathTime;                         // +0x70 ImmortalUntilDeathTime
	const FXList * m_invulnerableFX;                       // +0x74 InvulnerableFX
	Bool m_doHealthCheck;                                  // +0x78 DoHealthCheck
	const UpgradeTemplate * m_delayedDeathPrerequisiteUpgrade;// +0x7C DelayedDeathPrerequisiteUpgrade
};
// SIZE 0x80
typedef char DelayedDeathBodyModuleData_size[(sizeof(DelayedDeathBodyModuleData) == 0x80) ? 1 : -1];
typedef char DelayedDeathBodyModuleData_off_m_delayedDeathTime[(offsetof(DelayedDeathBodyModuleData, m_delayedDeathTime) == 0x6C) ? 1 : -1];
typedef char DelayedDeathBodyModuleData_off_m_immortalUntilDeathTime[(offsetof(DelayedDeathBodyModuleData, m_immortalUntilDeathTime) == 0x70) ? 1 : -1];
typedef char DelayedDeathBodyModuleData_off_m_invulnerableFX[(offsetof(DelayedDeathBodyModuleData, m_invulnerableFX) == 0x74) ? 1 : -1];
typedef char DelayedDeathBodyModuleData_off_m_doHealthCheck[(offsetof(DelayedDeathBodyModuleData, m_doHealthCheck) == 0x78) ? 1 : -1];
typedef char DelayedDeathBodyModuleData_off_m_delayedDeathPrerequisiteUpgrade[(offsetof(DelayedDeathBodyModuleData, m_delayedDeathPrerequisiteUpgrade) == 0x7C) ? 1 : -1];

#endif
