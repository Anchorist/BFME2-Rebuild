// MineshaftPortalBehaviour.h: the MineshaftPortalBehaviour module. SIZE 0x3C (ModuleFactory operator new).
// Target facts: the constructor 0x00373096 calls UpdateModule first; it stores the
// tables 0x00C1C780 at +0x20, 0x00C4EF80 at +0x24, 0x00C17DD0 at +0x0, 0x00C42B60 at +0xC, 0x00C17DC4 at +0x10, 0x00C17DC0 at +0x20, 0x00C17DB0 at +0x24. Members are what xfer (0x00373A0F) transfers after UpdateModule::xfer,
// typed by the Xfer slot each goes through, in that order; m_unk names are offsets
// (no map or donor name established). Bytes xfer does not touch are gaps.
// Not established: interface tables at +0x20, +0x24 (their vptrs sit in the gaps there).
// Not established: transfers xfer makes that this view cannot place: slot10 ?, slot4 ?, Char ?, UnsignedInt at misaligned +0x39, slot8 +0x39, slot4 ?.
#pragma once
#ifndef BFME2_MINESHAFT_PORTAL_BEHAVIOUR_H
#define BFME2_MINESHAFT_PORTAL_BEHAVIOUR_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/UpdateModule.h"

class Thing;
class ModuleData;
class Xfer;

// UpdateModule ends at 0x20; this class's members follow it.
typedef char MineshaftPortalBehaviour_base_size[(sizeof(UpdateModule) == 0x20) ? 1 : -1];

class MineshaftPortalBehaviour : public UpdateModule
{
public:
	MineshaftPortalBehaviour(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual void xfer(Xfer *xfer);

protected:
	virtual const char *GetSnapshotName() const;

public:
	UnsignedByte m_gap0x20[0x18];
	Bool m_unk0x38;                                // +0x38; xfer Bool
	Bool m_unk0x39;                                // +0x39; xfer Bool
protected:
	virtual void loadPostProcess() { UpdateModule::loadPostProcess(); }	// retail slot 1 0x00497805: a jmp to UpdateModule's
};
// SIZE 0x3C
typedef char MineshaftPortalBehaviour_size[(sizeof(MineshaftPortalBehaviour) == 0x3C) ? 1 : -1];
typedef char MineshaftPortalBehaviour_off_m_unk0x38[(offsetof(MineshaftPortalBehaviour, m_unk0x38) == 0x38) ? 1 : -1];
typedef char MineshaftPortalBehaviour_off_m_unk0x39[(offsetof(MineshaftPortalBehaviour, m_unk0x39) == 0x39) ? 1 : -1];

#endif
