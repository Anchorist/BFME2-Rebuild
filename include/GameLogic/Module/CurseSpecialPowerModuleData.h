// CurseSpecialPower configuration. The constructor at 0x004CCD34 installs the
// native data vtable and initializes both FX pointers and the curse multiplier.
// The parser at 0x004CCD64 adds three fields to the shared ability configuration.
#pragma once
#ifndef BFME2_CURSE_SPECIAL_POWER_MODULE_DATA_H
#define BFME2_CURSE_SPECIAL_POWER_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/SpecialAbilityUpdateModuleData.h"

class MultiIniFieldParse;
class FXList;

typedef char CurseSpecialPowerModuleData_base_size[(sizeof(SpecialAbilityUpdateModuleData) == 0xC8) ? 1 : -1];

class CurseSpecialPowerModuleData : public SpecialAbilityUpdateModuleData
{
public:
	CurseSpecialPowerModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);

	const FXList *m_triggerFX;                            // +0xC8 TriggerFX
	const FXList *m_cursedFX;                             // +0xCC CursedFX
	Real m_cursePercentage;                                // +0xD0 CursePercentage; percent
};
// SIZE 0xD4
typedef char CurseSpecialPowerModuleData_size[(sizeof(CurseSpecialPowerModuleData) == 0xD4) ? 1 : -1];
typedef char CurseSpecialPowerModuleData_off_m_triggerFX[(offsetof(CurseSpecialPowerModuleData, m_triggerFX) == 0xC8) ? 1 : -1];
typedef char CurseSpecialPowerModuleData_off_m_cursedFX[(offsetof(CurseSpecialPowerModuleData, m_cursedFX) == 0xCC) ? 1 : -1];
typedef char CurseSpecialPowerModuleData_off_m_cursePercentage[(offsetof(CurseSpecialPowerModuleData, m_cursePercentage) == 0xD0) ? 1 : -1];

#endif
