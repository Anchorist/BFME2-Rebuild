// RadiateFearUpdate.h: the RadiateFearUpdate module. SIZE 0x28 (ModuleFactory operator new).
// Target facts: the constructor 0x0049C106 calls UpdateModule first; it stores the
// tables 0x00C50FBC at +0x0, 0x00C49F78 at +0xC, 0x00C50FB0 at +0x10. Members are what xfer (0x0049C195) transfers after UpdateModule::xfer,
// typed by the Xfer slot each goes through, in that order; m_unk names are offsets
// (no map or donor name established). Bytes xfer does not touch are gaps.
// The constructor also builds an UpgradeMux at +0x20 (`lea edi,[esi+0x20]`,
// ??0UpgradeMux, then its table 0x00C50F68 stored through edi), so the class is UpdateModule +
// UpgradeMux; xfer transfers the mux through UpgradeMux::upgradeMuxXfer behind !IsLightCRC (the
// "slot10" the generator could not place). Table 0x00C50F68: slots 11 and 12 are this class's
// getUpgradeActivationMasks 0x0049C022 and performUpgradeFX 0x0049C049, 13/14 read the module data's
// RequiresAllTriggers/RequiresAllConflictingTriggers (0x0049C058/0x0049C062), 15 is performUpgradeFX
// again, 8 and 10 are bodies folded with other classes' (0x004B471F, 0x004A33E0).
#pragma once
#ifndef BFME2_RADIATE_FEAR_UPDATE_H
#define BFME2_RADIATE_FEAR_UPDATE_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/UpdateModule.h"
#include "GameLogic/Module/UpgradeModule.h"
#include "GameLogic/Module/RadiateFearUpdateModuleData.h"

class Thing;
class ModuleData;
class Xfer;

// UpdateModule ends at 0x20; this class's members follow it.
typedef char RadiateFearUpdate_base_size[(sizeof(UpdateModule) == 0x20) ? 1 : -1];

class RadiateFearUpdate : public UpdateModule, public UpgradeMux
{
public:
	virtual UpgradeModuleInterface *getUpgrade() { return this; }
	RadiateFearUpdate(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual UpdateSleepTime update();	// override: update slot 0 at +0x10 (0x0049C21E)

protected:
	virtual void loadPostProcess() { UpdateModule::loadPostProcess(); }	// retail slot 1 0x00497805: a jmp to UpdateModule's (table 0x00850FBC)
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

	// UpgradeMux (table 0x00C50F68 at +0x20)
	virtual void upgradeRemovalImplementation();						// slot 8 (folded body 0x004B471F)
	virtual void upgradeImplementation();								// slot 10 (folded body 0x004A33E0)
	virtual void getUpgradeActivationMasks(UpgradeMaskType &activation, UpgradeMaskType &conflicting) const;	// slot 11, 0x0049C022
	virtual void performUpgradeFX();									// slot 12, 0x0049C049
	virtual Bool requiresAllActivationUpgrades() const;					// slot 13, 0x0049C058
	virtual Bool requiresAllConflictingUpgrades() const;				// slot 14, 0x0049C062
	virtual void processUpgradeRemoval() { ((const RadiateFearUpdateModuleData *)getModuleData())->m_upgradeMuxData.muxDataProcessUpgradeRemoval(getObject()); }	// slot 15: retail 0x0049C049, ICF-folded with performUpgradeFX (both call the mux data's `ret 4` 0x0047A69C)
};
// SIZE 0x28
typedef char RadiateFearUpdate_mux_off[(sizeof(UpdateModule) + sizeof(UpgradeMux) == 0x28) ? 1 : -1];
typedef char RadiateFearUpdate_size[(sizeof(RadiateFearUpdate) == 0x28) ? 1 : -1];

#endif
