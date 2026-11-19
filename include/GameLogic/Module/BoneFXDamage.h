// BoneFXDamage: the damage module that goes with BoneFXUpdate (SAGE).
// Donor: Zero Hour GameLogic/Object/Damage/BoneFXDamage.cpp (callback bodies and names).
// Target facts: ctor 0x004B979C calls DamageModule's ctor 0x004B9704 and stores
// 0x00C598B4 at +0, 0x00C597F8 at +0x0C and 0x00C597E8 at +0x10, so the class adds no
// member to DamageModule. GetSnapshotName 0x004B96FE returns the literal "BoneFXDamage";
// the pool key 0x004B9757 interns the same name; onObjectCreated 0x004B97E2 and
// onBodyDamageStateChange 0x004B985E both look the object's BoneFXUpdate module up by
// name, the first throwing INIException(3) when it is missing.
#pragma once
#ifndef BFME2_BONEFXDAMAGE_H
#define BFME2_BONEFXDAMAGE_H

#include "GameLogic/Module/DamageModule.h"

class BoneFXDamage : public DamageModule
{
public:
	BoneFXDamage(Thing *thing, const ModuleData *moduleData);

	virtual NameKeyType getModuleNameKey() const;	// primary slot 4, 0x004B9757
	// DamageModuleInterface slots 0 and 1 use the native ret-4 fold 0x0047A69C.
	virtual void onDamage(DamageInfo *) {}
	virtual void onHealing(DamageInfo *) {}

	virtual void onBodyDamageStateChange(const DamageInfo *damageInfo,
		BodyDamageType oldState, BodyDamageType newState);

protected:
	virtual const char *GetSnapshotName() const;
	// The leaf writes its snapshot version before the base writes its own.
	virtual void xfer(Xfer *xfer)
	{
		xfer->Version1();
		DamageModule::xfer(xfer);
	}
	virtual void onObjectCreated();
	virtual void loadPostProcess() { DamageModule::loadPostProcess(); }	// retail slot 1 0x00497805: a jmp to DamageModule's (h05)
};

#endif /* BFME2_BONEFXDAMAGE_H */
