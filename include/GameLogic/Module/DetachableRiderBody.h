// An active body whose rider can detach when its upgrade state changes.
#pragma once
#ifndef BFME2_DETACHABLE_RIDER_BODY_H
#define BFME2_DETACHABLE_RIDER_BODY_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/ActiveBody.h"
#include "GameLogic/Module/UpgradeModule.h"
#include "GameLogic/Module/DetachableRiderBodyModuleData.h"

class Thing;
class ModuleData;
class Xfer;

// ActiveBody ends at 0x100; this class's members follow it.
typedef char DetachableRiderBody_base_size[(sizeof(ActiveBody) == 0x100) ? 1 : -1];

class DetachableRiderBody : public ActiveBody, public UpgradeMux
{
public:
	DetachableRiderBody(Thing *thing, const ModuleData *moduleData);
	static Module *friend_newModuleInstance(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual const char *GetSnapshotName() const;
	virtual void attemptDamage(DamageInfo *);	// override: attemptDamage slot 0 at +0x10 (0x004C1D49)
	virtual UpgradeMux *getUpgrade();				// slot 10: 0x004C1BD4, the null-preserving upcast to the UpgradeMux base at +0x100

protected:
	virtual void loadPostProcess() { ActiveBody::loadPostProcess(); }	// slot 1: retail 0x004C202F, a jmp to ActiveBody's (0x004BF40F), ICF-folded across the ActiveBody subclasses
	virtual void xfer(Xfer *xfer);

	// UpgradeMux (table 0x00C5BF00 at +0x100)
	virtual void upgradeRemovalImplementation();						// slot 8
	virtual void upgradeImplementation();								// slot 10
	virtual void getUpgradeActivationMasks(UpgradeMaskType &activation, UpgradeMaskType &conflicting) const;	// slot 11, 0x004C1C29
	virtual void performUpgradeFX();									// slot 12, 0x004C1C53
	virtual Bool requiresAllActivationUpgrades() const;					// slot 13, 0x004C1C68
	virtual Bool requiresAllConflictingUpgrades() const;				// slot 14, 0x004C1C75
	virtual void processUpgradeRemoval() { ((const DetachableRiderBodyModuleData *)getModuleData())->m_upgradeMuxData.muxDataProcessUpgradeRemoval(getObject()); }	// slot 15: retail 0x004C1C53, ICF-folded with performUpgradeFX (both call the mux data's `ret 4` 0x0047A69C)
};
// SIZE 0x108
typedef char DetachableRiderBody_size[(sizeof(DetachableRiderBody) == 0x108) ? 1 : -1];

#endif
