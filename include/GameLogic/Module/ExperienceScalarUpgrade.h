// ExperienceScalarUpgrade.h: the ExperienceScalarUpgrade upgrade module. SIZE 0x1C.
// Target facts: the constructor 0x004B61C6 calls UpgradeModule's constructor (0x00460AEC) and then
// installs the class's tables; the class adds no member of its own. upgradeImplementation (0x004B6213)
// adds the module data's AddXPScalar to the owning object's experience tracker scalar, and
// upgradeRemovalImplementation (0x004B6236) subtracts it again.
#pragma once
#ifndef BFME2_EXPERIENCE_SCALAR_UPGRADE_H
#define BFME2_EXPERIENCE_SCALAR_UPGRADE_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/UpgradeModule.h"

class Thing;
class ModuleData;
class Xfer;

// UpgradeModule ends at 0x1C; this class adds no member.
typedef char ExperienceScalarUpgrade_base_size[(sizeof(UpgradeModule) == 0x1C) ? 1 : -1];

class ExperienceScalarUpgrade : public UpgradeModule
{
public:
	ExperienceScalarUpgrade(Thing *thing, const ModuleData *moduleData);	// 0x004B61C6
	static Module *friend_newModuleInstance(Thing *thing, const ModuleData *moduleData);
	virtual ~ExperienceScalarUpgrade();
	virtual NameKeyType getModuleNameKey() const;

protected:
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);
	virtual void upgradeImplementation();
	virtual void upgradeRemovalImplementation();
protected:
	virtual void loadPostProcess() { UpgradeModule::loadPostProcess(); }	// retail slot 0x00497805: a jmp to UpgradeModule's, ICF-folded across classes
};
// SIZE 0x1C
typedef char ExperienceScalarUpgrade_size[(sizeof(ExperienceScalarUpgrade) == 0x1C) ? 1 : -1];

#endif
