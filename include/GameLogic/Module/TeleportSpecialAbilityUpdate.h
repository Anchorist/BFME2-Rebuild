// TeleportSpecialAbilityUpdate.h: the TeleportSpecialAbilityUpdate module. SIZE 0x88 (ModuleFactory operator new).
// Target facts: the constructor 0x00492C59 calls SpecialAbilityUpdate first; it stores the
// tables 0x00C4E1A8 at +0x0, 0x00C4D640 at +0xC, 0x00C4EB30 at +0x10, 0x00C4E184 at +0x20. Members are what xfer (0x00492E10) transfers after SpecialAbilityUpdate::xfer,
// typed by the Xfer slot each goes through, in that order; m_unk names are offsets
// (no map or donor name established). Bytes xfer does not touch are gaps.
#pragma once
#ifndef BFME2_TELEPORT_SPECIAL_ABILITY_UPDATE_H
#define BFME2_TELEPORT_SPECIAL_ABILITY_UPDATE_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/SpecialAbilityUpdate.h"

class Thing;
class ModuleData;
class Xfer;

// SpecialAbilityUpdate ends at 0x88; this class's members follow it.
typedef char TeleportSpecialAbilityUpdate_base_size[(sizeof(SpecialAbilityUpdate) == 0x88) ? 1 : -1];

class TeleportSpecialAbilityUpdate : public SpecialAbilityUpdate
{
public:
	static Module *friend_newModuleInstance(Thing *thing, const ModuleData *moduleData);
	TeleportSpecialAbilityUpdate(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual void triggerAbilityEffect();	// 0x00492D11
	virtual void startUnpacking();	// 0x00492DAB

protected:
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

public:
};
// SIZE 0x88
typedef char TeleportSpecialAbilityUpdate_size[(sizeof(TeleportSpecialAbilityUpdate) == 0x88) ? 1 : -1];

#endif
