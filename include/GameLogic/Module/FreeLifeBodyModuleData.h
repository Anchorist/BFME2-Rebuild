// The added life health, timing and animation settings.
#pragma once
#ifndef BFME2_FREE_LIFE_BODY_MODULE_DATA_H
#define BFME2_FREE_LIFE_BODY_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/RespawnBodyModuleData.h"
#include "GameLogic/Module/CustomAnimAndDuration.h"

class INI;
class MultiIniFieldParse;
class UpgradeTemplate;

// Base RespawnBodyModuleData: the constructor calls its constructor on this. It ends at 0x6C (its own operator-new size);
// this class's members follow it.
typedef char FreeLifeBodyModuleData_base_size[(sizeof(RespawnBodyModuleData) == 0x6C) ? 1 : -1];

class FreeLifeBodyModuleData : public RespawnBodyModuleData
{
public:
	FreeLifeBodyModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);

	Real m_freeLifeHealthPercent;                          // +0x6C FreeLifeHealthPercent; percent
	UnsignedInt m_freeLifeTime;                            // +0x70 FreeLifeTime; duration, frames
	Bool m_freeLifeInvincible;                             // +0x74 FreeLifeInvincible
	CustomAnimAndDuration m_freeLifeAnimAndDuration;	// Parsed by INI::iniParseAnimAndDuration.
	const UpgradeTemplate * m_freeLifePrerequisiteUpgrade; // +0x84 FreeLifePrerequisiteUpgrade
};
// SIZE 0x88
typedef char FreeLifeBodyModuleData_size[(sizeof(FreeLifeBodyModuleData) == 0x88) ? 1 : -1];
typedef char FreeLifeBodyModuleData_off_m_freeLifeHealthPercent[(offsetof(FreeLifeBodyModuleData, m_freeLifeHealthPercent) == 0x6C) ? 1 : -1];
typedef char FreeLifeBodyModuleData_off_m_freeLifeTime[(offsetof(FreeLifeBodyModuleData, m_freeLifeTime) == 0x70) ? 1 : -1];
typedef char FreeLifeBodyModuleData_off_m_freeLifeInvincible[(offsetof(FreeLifeBodyModuleData, m_freeLifeInvincible) == 0x74) ? 1 : -1];
typedef char FreeLifeBodyModuleData_off_m_freeLifeAnimAndDuration[(offsetof(FreeLifeBodyModuleData, m_freeLifeAnimAndDuration) == 0x78) ? 1 : -1];
typedef char FreeLifeBodyModuleData_off_m_freeLifePrerequisiteUpgrade[(offsetof(FreeLifeBodyModuleData, m_freeLifePrerequisiteUpgrade) == 0x84) ? 1 : -1];

#endif
