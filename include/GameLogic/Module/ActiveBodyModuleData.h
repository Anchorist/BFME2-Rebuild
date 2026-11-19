// ActiveBody's INI data. Field offsets come from the retail parse table.
// The runtime body copies the damage-effect list so it can apply effects on a hit
// or when a particular side is destroyed.
#pragma once
#ifndef BFME2_ACTIVE_BODY_MODULE_DATA_H
#define BFME2_ACTIVE_BODY_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/ModuleData.h"
#include "Common/AsciiString.h"
#include "Common/Coord2D.h"
#include <vector>

class INI;
class MultiIniFieldParse;
class FXList;
class ObjectCreationList;

// The INI name tables and snapshot transfers give these enum orders.
enum FXTrigger
{
	FX_TRIGGER_NONE,
	FX_TRIGGER_CATAPULT_ROCK,
	FX_TRIGGER_TREBUCHET_ROCK
};

enum BodySideDestroyedType
{
	BODY_SIDE_NONE,
	BODY_SIDE_FRONT_DESTROYED,
	BODY_SIDE_RIGHT_DESTROYED,
	BODY_SIDE_BACK_DESTROYED,
	BODY_SIDE_LEFT_DESTROYED
};

struct ActiveBodyDamageEffect
{
	const ObjectCreationList *m_ocl;
	FXTrigger m_trigger;
	BodySideDestroyedType m_destroyedSide;
};
typedef char ActiveBodyDamageEffect_size[(sizeof(ActiveBodyDamageEffect) == 0xC) ? 1 : -1];

class ActiveBodyModuleData : public ModuleData
{
public:
	ActiveBodyModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	virtual Bool slot07() const { return true; }

	Real m_maxHealth;                                      // +0x8 MaxHealth
	Real m_initialHealth;                                  // +0xC InitialHealth
	Real m_maxHealthDamaged;                               // +0x10 MaxHealthDamaged
	Real m_maxHealthReallyDamaged;                         // +0x14 MaxHealthReallyDamaged
	Real m_dodgePercent;                                   // +0x18 DodgePercent; percent
	UnsignedInt m_enteringDamagedTransitionTime;           // +0x1C EnteringDamagedTransitionTime; duration, frames
	UnsignedInt m_enteringReallyDamagedTransitionTime;     // +0x20 EnteringReallyDamagedTransitionTime; duration, frames
	UnsignedInt m_recoveryTime;                            // +0x24 RecoveryTime; duration, frames
	Bool m_useDefaultDamageSettings;                       // +0x28 UseDefaultDamageSettings
	AsciiString m_grabObject;                              // +0x2C GrabObject
	AsciiString m_damagedAttributeModifier;                // +0x30 DamagedAttributeModifier
	AsciiString m_reallyDamagedAttributeModifier;          // +0x34 ReallyDamagedAttributeModifier
	const FXList * m_grabFX;                               // +0x38 GrabFX
	Real m_grabDamage;                                     // +0x3C GrabDamage
	Coord2D m_grabOffset;                                  // +0x40 GrabOffset
	const FXList * m_healingBuffFx;                        // +0x48 HealingBuffFx
	Real m_cheerRadius;                                    // +0x4C CheerRadius
	Bool m_removeUpgradesOnDeath;                          // +0x50 RemoveUpgradesOnDeath
	Bool m_burningDeathBehavior;                           // +0x51 BurningDeathBehavior
	const FXList * m_burningDeathFX;                       // +0x54 BurningDeathFX
	std::vector<ActiveBodyDamageEffect> m_damageEffects;	// +0x58 (12 bytes); ActiveBody's constructor copies it to +0xE0
};
// SIZE 0x64
typedef char ActiveBodyModuleData_size[(sizeof(ActiveBodyModuleData) == 0x64) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_maxHealth[(offsetof(ActiveBodyModuleData, m_maxHealth) == 0x8) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_initialHealth[(offsetof(ActiveBodyModuleData, m_initialHealth) == 0xC) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_maxHealthDamaged[(offsetof(ActiveBodyModuleData, m_maxHealthDamaged) == 0x10) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_maxHealthReallyDamaged[(offsetof(ActiveBodyModuleData, m_maxHealthReallyDamaged) == 0x14) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_dodgePercent[(offsetof(ActiveBodyModuleData, m_dodgePercent) == 0x18) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_enteringDamagedTransitionTime[(offsetof(ActiveBodyModuleData, m_enteringDamagedTransitionTime) == 0x1C) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_enteringReallyDamagedTransitionTime[(offsetof(ActiveBodyModuleData, m_enteringReallyDamagedTransitionTime) == 0x20) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_recoveryTime[(offsetof(ActiveBodyModuleData, m_recoveryTime) == 0x24) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_useDefaultDamageSettings[(offsetof(ActiveBodyModuleData, m_useDefaultDamageSettings) == 0x28) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_grabObject[(offsetof(ActiveBodyModuleData, m_grabObject) == 0x2C) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_damagedAttributeModifier[(offsetof(ActiveBodyModuleData, m_damagedAttributeModifier) == 0x30) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_reallyDamagedAttributeModifier[(offsetof(ActiveBodyModuleData, m_reallyDamagedAttributeModifier) == 0x34) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_grabFX[(offsetof(ActiveBodyModuleData, m_grabFX) == 0x38) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_grabDamage[(offsetof(ActiveBodyModuleData, m_grabDamage) == 0x3C) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_grabOffset[(offsetof(ActiveBodyModuleData, m_grabOffset) == 0x40) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_healingBuffFx[(offsetof(ActiveBodyModuleData, m_healingBuffFx) == 0x48) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_cheerRadius[(offsetof(ActiveBodyModuleData, m_cheerRadius) == 0x4C) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_removeUpgradesOnDeath[(offsetof(ActiveBodyModuleData, m_removeUpgradesOnDeath) == 0x50) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_burningDeathBehavior[(offsetof(ActiveBodyModuleData, m_burningDeathBehavior) == 0x51) ? 1 : -1];
typedef char ActiveBodyModuleData_off_m_burningDeathFX[(offsetof(ActiveBodyModuleData, m_burningDeathFX) == 0x54) ? 1 : -1];

#endif
