// Configuration for stopping an active special power.
#pragma once
#ifndef BFME2_STOP_SPECIAL_POWER_MODULE_DATA_H
#define BFME2_STOP_SPECIAL_POWER_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/SpecialPowerModuleData.h"

class INI;
class MultiIniFieldParse;
class SpecialPowerTemplate;

// Base SpecialPowerModuleData: the constructor calls its constructor on this. It ends at 0x7C (its own operator-new size);
// this class's members follow it.
typedef char StopSpecialPowerModuleData_base_size[(sizeof(SpecialPowerModuleData) == 0x7C) ? 1 : -1];

class StopSpecialPowerModuleData : public SpecialPowerModuleData
{
public:
	StopSpecialPowerModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);

	const SpecialPowerTemplate * m_stopPowerTemplate;      // +0x7C StopPowerTemplate
};
// SIZE 0x80
typedef char StopSpecialPowerModuleData_size[(sizeof(StopSpecialPowerModuleData) == 0x80) ? 1 : -1];
typedef char StopSpecialPowerModuleData_off_m_stopPowerTemplate[(offsetof(StopSpecialPowerModuleData, m_stopPowerTemplate) == 0x7C) ? 1 : -1];

#endif
