#pragma once
#ifndef BFME2_UNTAMED_ALLEGIANCE_SPECIAL_POWER_MODULE_DATA_H
#define BFME2_UNTAMED_ALLEGIANCE_SPECIAL_POWER_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/SpecialPowerModuleData.h"

class MultiIniFieldParse;

// This module adds no storage to the shared special-power data.
class UntamedAllegianceSpecialPowerModuleData : public SpecialPowerModuleData
{
public:
	UntamedAllegianceSpecialPowerModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
};
typedef char UntamedAllegianceSpecialPowerModuleData_size[(sizeof(UntamedAllegianceSpecialPowerModuleData) == 0x7C) ? 1 : -1];

#endif
