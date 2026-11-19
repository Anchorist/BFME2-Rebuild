// An update module that applies an attribute modifier through its aura.
#pragma once
#ifndef BFME2_ATTRIBUTE_MODIFIER_AURA_UPDATE_H
#define BFME2_ATTRIBUTE_MODIFIER_AURA_UPDATE_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/UpdateModule.h"
#include "GameLogic/Module/UpgradeModule.h"
#include "GameLogic/Module/AttributeModifierAuraUpdateModuleData.h"

class Thing;
class ModuleData;
class Xfer;

// UpdateModule ends at 0x20; this class's members follow it.
typedef char AttributeModifierAuraUpdate_base_size[(sizeof(UpdateModule) == 0x20) ? 1 : -1];

class AttributeModifierAuraUpdate : public UpdateModule, public UpgradeMux
{
public:
	AttributeModifierAuraUpdate(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual UpdateSleepTime update();	// override: update slot 0 at +0x10 (0x0049BCA3)

protected:
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

	// UpgradeMux (table 0x00C50CD8 at +0x20)
	virtual void upgradeRemovalImplementation();						// slot 8
	virtual void upgradeImplementation();								// slot 10
	virtual void getUpgradeActivationMasks(UpgradeMaskType &activation, UpgradeMaskType &conflicting) const;	// slot 11, 0x0049B621
	virtual void performUpgradeFX();									// slot 12, 0x0049B648
	virtual Bool requiresAllActivationUpgrades() const;					// slot 13
	virtual Bool requiresAllConflictingUpgrades() const;				// slot 14
	virtual void processUpgradeRemoval() { ((const AttributeModifierAuraUpdateModuleData *)getModuleData())->m_upgradeMuxData.muxDataProcessUpgradeRemoval(getObject()); }	// slot 15: retail 0x0049B648, ICF-folded with performUpgradeFX (both call the mux data's `ret 4` 0x0047A69C)
protected:
	virtual void loadPostProcess() { UpdateModule::loadPostProcess(); }	// retail slot 1 0x00497805: a jmp to UpdateModule's (h05)
};
// SIZE 0x28
typedef char AttributeModifierAuraUpdate_size[(sizeof(AttributeModifierAuraUpdate) == 0x28) ? 1 : -1];

#endif
