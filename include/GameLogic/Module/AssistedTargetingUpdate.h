// AssistedTargetingUpdate: the AssistedTargetingUpdate update module, UpdateModule with no members of its own (SIZE 0x20).
// The constructor runs UpdateModule's constructor and installs the module's three tables; the destructor
// puts the UpdateModule tables back and jumps to UpdateModule's destructor; xfer saves only the base.
#pragma once
#ifndef BFME2_ASSISTED_TARGETING_UPDATE_H
#define BFME2_ASSISTED_TARGETING_UPDATE_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/UpdateModule.h"

class Thing;
class ModuleData;
class Xfer;
class Object;
class ThingTemplate;

// UpdateModule ends at 0x20; this class's members follow it.
typedef char AssistedTargetingUpdate_base_size[(sizeof(UpdateModule) == 0x20) ? 1 : -1];

class AssistedTargetingUpdate : public UpdateModule
{
public:
	AssistedTargetingUpdate(Thing *thing, const ModuleData *moduleData);
	virtual ~AssistedTargetingUpdate();
	virtual NameKeyType getModuleNameKey() const;
	virtual UpdateSleepTime update();								// +0x10 slot 0, 0x004A6563
	Bool isFreeToAssist() const;
	void assistAttack(const Object *victim, Object *target);

protected:
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

private:
	void makeFeedbackLaser(const ThingTemplate *laser, const Object *from, const Object *to);
protected:
	virtual void loadPostProcess() { UpdateModule::loadPostProcess(); }	// retail slot 0x00497805: a jmp to UpdateModule's, ICF-folded across classes
};
// SIZE 0x20
typedef char AssistedTargetingUpdate_size[(sizeof(AssistedTargetingUpdate) == 0x20) ? 1 : -1];

#endif
