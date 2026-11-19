// The levels an upgrade grants and its upper limit.
#pragma once
#ifndef BFME2_LEVEL_UP_UPGRADE_MODULE_DATA_H
#define BFME2_LEVEL_UP_UPGRADE_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/UpgradeModule.h"

class INI;
class MultiIniFieldParse;

class LevelUpUpgradeModuleData : public UpgradeModuleData
{
public:
	LevelUpUpgradeModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	virtual Bool slot12() const { return true; }

	Int m_levelsToGain;                                    // +0x118 LevelsToGain
	Int m_levelCap;                                        // +0x11C LevelCap
};
// SIZE 0x120
typedef char LevelUpUpgradeModuleData_size[(sizeof(LevelUpUpgradeModuleData) == 0x120) ? 1 : -1];
typedef char LevelUpUpgradeModuleData_off_m_levelsToGain[(offsetof(LevelUpUpgradeModuleData, m_levelsToGain) == 0x118) ? 1 : -1];
typedef char LevelUpUpgradeModuleData_off_m_levelCap[(offsetof(LevelUpUpgradeModuleData, m_levelCap) == 0x11C) ? 1 : -1];

#endif
