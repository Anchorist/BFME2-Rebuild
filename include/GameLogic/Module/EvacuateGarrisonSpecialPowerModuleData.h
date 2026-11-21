#pragma once
#ifndef BFME2_EVACUATE_GARRISON_SPECIAL_POWER_MODULE_DATA_H
#define BFME2_EVACUATE_GARRISON_SPECIAL_POWER_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/SpecialAbilityUpdateModuleData.h"

class MultiIniFieldParse;

// This module adds no storage to the shared special-ability data.
class EvacuateGarrisonSpecialPowerModuleData : public SpecialAbilityUpdateModuleData
{
public:
	EvacuateGarrisonSpecialPowerModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);
};
typedef char EvacuateGarrisonSpecialPowerModuleData_size[(sizeof(EvacuateGarrisonSpecialPowerModuleData) == 0xC8) ? 1 : -1];

#endif
