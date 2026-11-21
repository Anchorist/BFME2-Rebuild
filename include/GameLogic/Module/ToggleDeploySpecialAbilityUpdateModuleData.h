// Sound references for entering and leaving deployment.
#pragma once
#ifndef BFME2_TOGGLE_DEPLOY_SPECIAL_ABILITY_UPDATE_MODULE_DATA_H
#define BFME2_TOGGLE_DEPLOY_SPECIAL_ABILITY_UPDATE_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/SpecialAbilityUpdateModuleData.h"
#include "Common/OpaqueRefElement4.h"

class INI;
class MultiIniFieldParse;

// Base SpecialAbilityUpdateModuleData: the constructor calls its constructor on this. It ends at 0xC8 (its own operator-new size);
// this class's members follow it.
typedef char ToggleDeploySpecialAbilityUpdateModuleData_base_size[(sizeof(SpecialAbilityUpdateModuleData) == 0xC8) ? 1 : -1];

class ToggleDeploySpecialAbilityUpdateModuleData : public SpecialAbilityUpdateModuleData
{
public:
	ToggleDeploySpecialAbilityUpdateModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);

	OpaqueRefElement4 m_soundDeploy;                      // +0xC8 SoundDeploy (turnOn 0x004AE6D7 builds an AudioEventRTS from it)
	OpaqueRefElement4 m_soundUndeploy;                    // +0xCC SoundUndeploy (turnOff 0x004AE5B8 builds an AudioEventRTS from it)
};
// SIZE 0xD0
typedef char ToggleDeploySpecialAbilityUpdateModuleData_size[(sizeof(ToggleDeploySpecialAbilityUpdateModuleData) == 0xD0) ? 1 : -1];
typedef char ToggleDeploySpecialAbilityUpdateModuleData_off_m_soundDeploy[(offsetof(ToggleDeploySpecialAbilityUpdateModuleData, m_soundDeploy) == 0xC8) ? 1 : -1];
typedef char ToggleDeploySpecialAbilityUpdateModuleData_off_m_soundUndeploy[(offsetof(ToggleDeploySpecialAbilityUpdateModuleData, m_soundUndeploy) == 0xCC) ? 1 : -1];

#endif
