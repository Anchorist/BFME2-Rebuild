// FreezingRainSpecialPowerModuleData extends SpecialPowerModuleData with the fields below.
// Retail parser 0x4C4B86 adds table 0x85D6C0 after the inherited fields.
#pragma once
#ifndef BFME2_FREEZING_RAIN_SPECIAL_POWER_MODULE_DATA_H
#define BFME2_FREEZING_RAIN_SPECIAL_POWER_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/SpecialPowerModuleData.h"

class FXList;

// Base SpecialPowerModuleData: the constructor calls its constructor on this. It ends at 0x7C (its own operator-new size);
// this class's members follow it.
typedef char FreezingRainSpecialPowerModuleData_base_size[(sizeof(SpecialPowerModuleData) == 0x7C) ? 1 : -1];

class FreezingRainSpecialPowerModuleData : public SpecialPowerModuleData
{
public:
	FreezingRainSpecialPowerModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);

	Real m_freezingRainRadius;                             // +0x7C FreezingRainRadius
	const FXList *m_freezingRainFX;                       // +0x80 FreezingRainFX
	Int m_burnRateModifier;                                // +0x84 BurnRateModifier
};
// SIZE 0x88
typedef char FreezingRainSpecialPowerModuleData_size[(sizeof(FreezingRainSpecialPowerModuleData) == 0x88) ? 1 : -1];
typedef char FreezingRainSpecialPowerModuleData_off_m_freezingRainRadius[(offsetof(FreezingRainSpecialPowerModuleData, m_freezingRainRadius) == 0x7C) ? 1 : -1];
typedef char FreezingRainSpecialPowerModuleData_off_m_freezingRainFX[(offsetof(FreezingRainSpecialPowerModuleData, m_freezingRainFX) == 0x80) ? 1 : -1];
typedef char FreezingRainSpecialPowerModuleData_off_m_burnRateModifier[(offsetof(FreezingRainSpecialPowerModuleData, m_burnRateModifier) == 0x84) ? 1 : -1];

#endif
