// Configuration for timed deposits, capture bonuses and the upgrade filter.
#pragma once
#ifndef BFME2_AUTO_DEPOSIT_UPDATE_MODULE_DATA_H
#define BFME2_AUTO_DEPOSIT_UPDATE_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/ModuleData.h"
#include "GameLogic/ObjectFilter.h"

class INI;
class MultiIniFieldParse;
class UpgradeTemplate;

class AutoDepositUpdateModuleData : public ModuleData
{
public:
	AutoDepositUpdateModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);

	UnsignedInt m_depositTiming;                           // +0x8 DepositTiming; duration, frames
	Int m_depositAmount;                                   // +0xC DepositAmount
	Int m_initialCaptureBonus;                             // +0x10 InitialCaptureBonus
	const UpgradeTemplate * m_upgrade;                     // +0x14 Upgrade
	Real m_upgradeBonusPercent;                            // +0x18 UpgradeBonusPercent; percent
	ObjectFilter m_upgradeMustBePresent;                   // +0x1C UpgradeMustBePresent
	Bool m_giveNoXP;                                       // +0x20 GiveNoXP
	Bool m_onlyWhenGarrisoned;                             // +0x21 OnlyWhenGarrisoned
};
// SIZE 0x24
typedef char AutoDepositUpdateModuleData_size[(sizeof(AutoDepositUpdateModuleData) == 0x24) ? 1 : -1];
typedef char AutoDepositUpdateModuleData_off_m_depositTiming[(offsetof(AutoDepositUpdateModuleData, m_depositTiming) == 0x8) ? 1 : -1];
typedef char AutoDepositUpdateModuleData_off_m_depositAmount[(offsetof(AutoDepositUpdateModuleData, m_depositAmount) == 0xC) ? 1 : -1];
typedef char AutoDepositUpdateModuleData_off_m_initialCaptureBonus[(offsetof(AutoDepositUpdateModuleData, m_initialCaptureBonus) == 0x10) ? 1 : -1];
typedef char AutoDepositUpdateModuleData_off_m_upgrade[(offsetof(AutoDepositUpdateModuleData, m_upgrade) == 0x14) ? 1 : -1];
typedef char AutoDepositUpdateModuleData_off_m_upgradeBonusPercent[(offsetof(AutoDepositUpdateModuleData, m_upgradeBonusPercent) == 0x18) ? 1 : -1];
typedef char AutoDepositUpdateModuleData_off_m_upgradeMustBePresent[(offsetof(AutoDepositUpdateModuleData, m_upgradeMustBePresent) == 0x1C) ? 1 : -1];
typedef char AutoDepositUpdateModuleData_off_m_giveNoXP[(offsetof(AutoDepositUpdateModuleData, m_giveNoXP) == 0x20) ? 1 : -1];
typedef char AutoDepositUpdateModuleData_off_m_onlyWhenGarrisoned[(offsetof(AutoDepositUpdateModuleData, m_onlyWhenGarrisoned) == 0x21) ? 1 : -1];

#endif
