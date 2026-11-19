// Configuration for the scavenger bounty.
#pragma once
#ifndef BFME2_SCAVENGER_SPECIAL_POWER_MODULE_DATA_H
#define BFME2_SCAVENGER_SPECIAL_POWER_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/SpecialPowerModuleData.h"

class INI;
class MultiIniFieldParse;

// Base SpecialPowerModuleData: the constructor calls its constructor on this. It ends at 0x7C (its own operator-new size);
// this class's members follow it.
typedef char ScavengerSpecialPowerModuleData_base_size[(sizeof(SpecialPowerModuleData) == 0x7C) ? 1 : -1];

class ScavengerSpecialPowerModuleData : public SpecialPowerModuleData
{
public:
	ScavengerSpecialPowerModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);

	Real m_bountyPercent;                                  // +0x7C BountyPercent
};
// SIZE 0x80
typedef char ScavengerSpecialPowerModuleData_size[(sizeof(ScavengerSpecialPowerModuleData) == 0x80) ? 1 : -1];
typedef char ScavengerSpecialPowerModuleData_off_m_bountyPercent[(offsetof(ScavengerSpecialPowerModuleData, m_bountyPercent) == 0x7C) ? 1 : -1];

#endif
