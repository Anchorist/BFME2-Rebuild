// Constructor 0x00482D80 builds UpdateModule at +0x0, UpgradeMux at +0x20,
// and DieModuleInterface at +0x28. Destructor 0x00482E96 restores their
// tables before entering ~UpdateModule. Xfer 0x00482BDB transfers the
// DamageInfo at +0x2C and its delay at +0xA8 from version 3 onward.
#pragma once
#ifndef BFME2_FIRE_WEAPON_WHEN_DEAD_BEHAVIOR_H
#define BFME2_FIRE_WEAPON_WHEN_DEAD_BEHAVIOR_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/UpdateModule.h"
#include "GameLogic/Module/UpgradeModule.h"
#include "GameLogic/Module/FireWeaponWhenDeadBehaviorModuleData.h"
#include "GameLogic/Module/DieModuleInterface.h"
#include "GameLogic/Damage.h"

class Thing;
class ModuleData;
class Xfer;

// UpdateModule ends at 0x20; this class's members follow it.
typedef char FireWeaponWhenDeadBehavior_base_size[(sizeof(UpdateModule) == 0x20) ? 1 : -1];

class FireWeaponWhenDeadBehavior : public UpdateModule, public UpgradeMux, public DieModuleInterface
{
public:
	virtual DieModuleInterface *getDie() { return this; }
	virtual UpgradeModuleInterface *getUpgrade() { return this; }
	FireWeaponWhenDeadBehavior(Thing *thing, const ModuleData *moduleData);
	static Module *friend_newModuleInstance(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual const char *GetSnapshotName() const;
	virtual ~FireWeaponWhenDeadBehavior();
	virtual void loadPostProcess();	// override: loadPostProcess slot 1 at +0x0 (0x00482C39)
	virtual DisabledMaskType getDisabledTypesToProcess() const;	// override: getDisabledTypesToProcess slot 64 at +0xC (0x004DF396)
	virtual UpdateSleepTime update();	// override: update slot 0 at +0x10 (0x00482BB9)
	virtual void onDie(const DamageInfo *damageInfo);	// DieModuleInterface slot 0 at +0x28 (0x00482C4A)

protected:
	virtual void xfer(Xfer *xfer);

	// UpgradeMux (table 0x00C496A0 at +0x20)
	virtual void upgradeRemovalImplementation();
	virtual void upgradeImplementation();
	virtual void getUpgradeActivationMasks(UpgradeMaskType &activation, UpgradeMaskType &conflicting) const;
	virtual void performUpgradeFX();
	virtual Bool requiresAllActivationUpgrades() const;
	virtual Bool requiresAllConflictingUpgrades() const;
	virtual void processUpgradeRemoval() { ((const FireWeaponWhenDeadBehaviorModuleData *)getModuleData())->m_upgradeMuxData.muxDataProcessUpgradeRemoval(getObject()); }	// slot 15: retail 0x00452487, ICF-folded with performUpgradeFX (both call the mux data's `ret 4` 0x0047A69C)

public:
	DamageInfo m_deathDamage;									// +0x2C: built by the constructor (0x00263895), transferred through its slot 0 by xfer 0x00482BDB
	Int m_delayFrames;                             // +0xA8; xfer Int, the constructor sets it from the module data's DelayTime
};
// SIZE 0xAC
typedef char FireWeaponWhenDeadBehavior_size[(sizeof(FireWeaponWhenDeadBehavior) == 0xAC) ? 1 : -1];
typedef char FireWeaponWhenDeadBehavior_off_m_delayFrames[(offsetof(FireWeaponWhenDeadBehavior, m_delayFrames) == 0xA8) ? 1 : -1];

#endif
