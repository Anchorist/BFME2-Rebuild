// ProductionSpeedBonus INI data. Retail 0x004C2FE6 constructs the 0x90-byte type
// and installs table 0x00C5CA80. The three fields follow the native 0x7C-byte base.
#pragma once
#ifndef BFME2_PRODUCTION_SPEED_BONUS_MODULE_DATA_H
#define BFME2_PRODUCTION_SPEED_BONUS_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/SpecialPowerModuleData.h"
#include "Common/AsciiString.h"
#include "Common/Vector.h"

class MultiIniFieldParse;

// Base SpecialPowerModuleData: the constructor calls its constructor on this. It ends at 0x7C (its own operator-new size);
// this class's members follow it.
typedef char ProductionSpeedBonusModuleData_base_size[(sizeof(SpecialPowerModuleData) == 0x7C) ? 1 : -1];

class ProductionSpeedBonusModuleData : public SpecialPowerModuleData
{
public:
	ProductionSpeedBonusModuleData();
	virtual ~ProductionSpeedBonusModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);

	Int m_numberOfFrames;                                  // +0x7C NumberOfFrames
	Real m_speedMultiplier;                                // +0x80 SpeedMulitplier
	_STL::vector<AsciiString> m_types;                      // +0x84 Type
};
// SIZE 0x90
typedef char ProductionSpeedBonusModuleData_size[(sizeof(ProductionSpeedBonusModuleData) == 0x90) ? 1 : -1];
typedef char ProductionSpeedBonusModuleData_off_m_numberOfFrames[(offsetof(ProductionSpeedBonusModuleData, m_numberOfFrames) == 0x7C) ? 1 : -1];
typedef char ProductionSpeedBonusModuleData_off_m_speedMultiplier[(offsetof(ProductionSpeedBonusModuleData, m_speedMultiplier) == 0x80) ? 1 : -1];
typedef char ProductionSpeedBonusModuleData_off_m_types[(offsetof(ProductionSpeedBonusModuleData, m_types) == 0x84) ? 1 : -1];

#endif
