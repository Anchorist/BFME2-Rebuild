// The formation data has two weapon templates and a byte-sized crusher level.
// Retail parser 0x4C1FCB adds table 0x85C2D8 after the ActiveBody fields.
#pragma once
#ifndef BFME2_PORCUPINE_FORMATION_BODY_MODULE_DATA_H
#define BFME2_PORCUPINE_FORMATION_BODY_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/ActiveBodyModuleData.h"

class INI;
class WeaponTemplate;

// Base ActiveBodyModuleData: the constructor calls its constructor on this. It ends at 0x64 (its own operator-new size);
// this class's members follow it.
typedef char PorcupineFormationBodyModuleData_base_size[(sizeof(ActiveBodyModuleData) == 0x64) ? 1 : -1];

class PorcupineFormationBodyModuleData : public ActiveBodyModuleData
{
public:
	PorcupineFormationBodyModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);

	const WeaponTemplate *m_damageWeaponTemplate;         // +0x64 DamageWeaponTemplate
	const WeaponTemplate *m_crushDamageWeaponTemplate;    // +0x68 CrushDamageWeaponTemplate
	Byte m_crusherLevelResisted;                           // +0x6C CrusherLevelResisted
};
// Retail factory 0x25180A calls the emitted 29-byte constructor at 0x4C225D.
inline PorcupineFormationBodyModuleData::PorcupineFormationBodyModuleData() :
	m_damageWeaponTemplate(0),
	m_crushDamageWeaponTemplate(0),
	m_crusherLevelResisted(0)
{
}

typedef char PorcupineFormationBodyModuleData_size[(sizeof(PorcupineFormationBodyModuleData) == 0x70) ? 1 : -1];
typedef char PorcupineFormationBodyModuleData_off_m_damageWeaponTemplate[(offsetof(PorcupineFormationBodyModuleData, m_damageWeaponTemplate) == 0x64) ? 1 : -1];
typedef char PorcupineFormationBodyModuleData_off_m_crushDamageWeaponTemplate[(offsetof(PorcupineFormationBodyModuleData, m_crushDamageWeaponTemplate) == 0x68) ? 1 : -1];
typedef char PorcupineFormationBodyModuleData_off_m_crusherLevelResisted[(offsetof(PorcupineFormationBodyModuleData, m_crusherLevelResisted) == 0x6C) ? 1 : -1];

#endif
