// ScaleWallSpecialAbilityUpdate.h: the ScaleWallSpecialAbilityUpdate module. SIZE 0x88 (ModuleFactory operator new).
// Target facts: the constructor 0x00494DCA calls SpecialAbilityUpdate first; it stores the
// tables 0x00C4EB40 at +0x0, 0x00C4D640 at +0xC, 0x00C4EB30 at +0x10, 0x00C4EB0C at +0x20. Members are what xfer (0x00494E57) transfers after SpecialAbilityUpdate::xfer,
// typed by the Xfer slot each goes through, in that order; m_unk names are offsets
// (no map or donor name established). Bytes xfer does not touch are gaps.
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
	virtual void triggerAbilityEffect();	// 0x00494E26

protected:
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

public:
};
// SIZE 0x88
typedef char ScaleWallSpecialAbilityUpdate_size[(sizeof(ScaleWallSpecialAbilityUpdate) == 0x88) ? 1 : -1];

#endif
