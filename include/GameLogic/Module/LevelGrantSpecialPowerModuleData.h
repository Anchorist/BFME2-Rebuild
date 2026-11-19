// LevelGrantSpecialPowerModuleData extends SpecialAbilityUpdateModuleData with the fields below.
// Retail parser 0x4C2AF3 adds table 0x85C8D0 after the inherited fields.
#pragma once
#ifndef BFME2_LEVEL_GRANT_SPECIAL_POWER_MODULE_DATA_H
#define BFME2_LEVEL_GRANT_SPECIAL_POWER_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/SpecialAbilityUpdateModuleData.h"
#include "GameLogic/ObjectFilter.h"

class FXList;

// Base SpecialAbilityUpdateModuleData: the constructor calls its constructor on this. It ends at 0xC8 (its own operator-new size);
// this class's members follow it.
typedef char LevelGrantSpecialPowerModuleData_base_size[(sizeof(SpecialAbilityUpdateModuleData) == 0xC8) ? 1 : -1];

class LevelGrantSpecialPowerModuleData : public SpecialAbilityUpdateModuleData
{
public:
	LevelGrantSpecialPowerModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);

	Int m_experience;                                      // +0xC8 Experience
	Real m_radiusEffect;                                   // +0xCC RadiusEffect
	ObjectFilter m_acceptanceFilter;                       // +0xD0 AcceptanceFilter
	const FXList *m_levelFX;                              // +0xD4 LevelFX
};
// SIZE 0xD8
typedef char LevelGrantSpecialPowerModuleData_size[(sizeof(LevelGrantSpecialPowerModuleData) == 0xD8) ? 1 : -1];
typedef char LevelGrantSpecialPowerModuleData_off_m_experience[(offsetof(LevelGrantSpecialPowerModuleData, m_experience) == 0xC8) ? 1 : -1];
typedef char LevelGrantSpecialPowerModuleData_off_m_radiusEffect[(offsetof(LevelGrantSpecialPowerModuleData, m_radiusEffect) == 0xCC) ? 1 : -1];
typedef char LevelGrantSpecialPowerModuleData_off_m_acceptanceFilter[(offsetof(LevelGrantSpecialPowerModuleData, m_acceptanceFilter) == 0xD0) ? 1 : -1];
typedef char LevelGrantSpecialPowerModuleData_off_m_levelFX[(offsetof(LevelGrantSpecialPowerModuleData, m_levelFX) == 0xD4) ? 1 : -1];

#endif
