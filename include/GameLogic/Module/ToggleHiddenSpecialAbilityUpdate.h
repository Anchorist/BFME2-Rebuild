// ToggleHiddenSpecialAbilityUpdate extends SpecialAbilityUpdate with its activation frame.
// turnOn records the game frame at 0x004AE42A and update at 0x004AE286 adds
// the configured duration before deciding when to turn the ability off.
#pragma once
#ifndef BFME2_TOGGLE_HIDDEN_SPECIAL_ABILITY_UPDATE_H
#define BFME2_TOGGLE_HIDDEN_SPECIAL_ABILITY_UPDATE_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/SpecialAbilityUpdate.h"

class Thing;
class ModuleData;
class Xfer;

// SpecialAbilityUpdate ends at 0x88; this class's members follow it.
typedef char ToggleHiddenSpecialAbilityUpdate_base_size[(sizeof(SpecialAbilityUpdate) == 0x88) ? 1 : -1];

class ToggleHiddenSpecialAbilityUpdate : public SpecialAbilityUpdate
{
public:
	ToggleHiddenSpecialAbilityUpdate(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual void triggerAbilityEffect();	// override: triggerAbilityEffect slot 17 at +0x0 (0x004AE22D)
	virtual UpdateSleepTime update();	// override: update slot 0 at +0x10 (0x004AE286)
	virtual void turnOff();	// slot 23 (0x004AE2D0); StealthUpdate rva00373D5E 0x00373D5E calls it through [vtable+0x5C]
	virtual void turnOn();	// slot 24 (0x004AE394)
	virtual Int rva0021914D() const;	// slot 25 (0x0021914D, map: ?get@Rva0021914DDwordField@@QBEHXZ); StealthUpdate 0x00373F59 compares the body's last damage frame with it

protected:
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

public:
	UnsignedInt m_activationFrame;                         // +0x88, stored by turnOn and serialized by xfer
protected:
	virtual void loadPostProcess() { SpecialAbilityUpdate::loadPostProcess(); }	// retail slot 1 0x00483CEF: a jmp to SpecialAbilityUpdate's
};
// SIZE 0x8C
typedef char ToggleHiddenSpecialAbilityUpdate_size[(sizeof(ToggleHiddenSpecialAbilityUpdate) == 0x8C) ? 1 : -1];
typedef char ToggleHiddenSpecialAbilityUpdate_off_m_activationFrame[(offsetof(ToggleHiddenSpecialAbilityUpdate, m_activationFrame) == 0x88) ? 1 : -1];

#endif
