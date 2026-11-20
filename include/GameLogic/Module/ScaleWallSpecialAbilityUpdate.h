// ScaleWallSpecialAbilityUpdate: the ScaleWall special ability. It adds no data to SpecialAbilityUpdate (SIZE 0x88):
// its constructor (0x00494DCA) runs the base constructor and installs this class's tables, and its xfer (0x00494E57)
// saves only what the base saves. It overrides the module name key, the snapshot name and triggerAbilityEffect.
#pragma once
#ifndef BFME2_SCALE_WALL_SPECIAL_ABILITY_UPDATE_H
#define BFME2_SCALE_WALL_SPECIAL_ABILITY_UPDATE_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/SpecialAbilityUpdate.h"

class Thing;
class ModuleData;
class Xfer;

// SpecialAbilityUpdate ends at 0x88; this class's members follow it.
typedef char ScaleWallSpecialAbilityUpdate_base_size[(sizeof(SpecialAbilityUpdate) == 0x88) ? 1 : -1];

class ScaleWallSpecialAbilityUpdate : public SpecialAbilityUpdate
{
public:
	static Module *friend_newModuleInstance(Thing *thing, const ModuleData *moduleData);
	ScaleWallSpecialAbilityUpdate(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual void triggerAbilityEffect();

protected:
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

public:
};
// SIZE 0x88
typedef char ScaleWallSpecialAbilityUpdate_size[(sizeof(ScaleWallSpecialAbilityUpdate) == 0x88) ? 1 : -1];

#endif
