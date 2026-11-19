// ClickReactionBehavior.h: the ClickReactionBehavior module. SIZE 0x2C (ModuleFactory operator new).
// Target facts: the constructor 0x0045961D calls UpdateModule first; it stores the
// tables 0x00BE2B78 at +0x20, 0x00C4125C at +0x0, 0x00C411A0 at +0xC, 0x00C41194 at +0x10, 0x00C41188 at +0x20. Members are what xfer (0x00459579) transfers after UpdateModule::xfer,
// typed by the Xfer slot each goes through, in that order; m_unk names are offsets
// (no map or donor name established). Bytes xfer does not touch are gaps.
// Not established: interface tables at +0x20 (their vptrs sit in the gaps there).
#pragma once
#ifndef BFME2_CLICK_REACTION_BEHAVIOR_H
#define BFME2_CLICK_REACTION_BEHAVIOR_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/UpdateModule.h"

class Thing;
class ModuleData;
class Xfer;

// UpdateModule ends at 0x20; this class's members follow it.
typedef char ClickReactionBehavior_base_size[(sizeof(UpdateModule) == 0x20) ? 1 : -1];

class ClickReactionBehavior : public UpdateModule
{
public:
	ClickReactionBehavior(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual const char *GetSnapshotName() const;

protected:
	virtual void xfer(Xfer *xfer);

public:
	UnsignedByte m_gap0x20[0x4];
	Int m_unk0x24;                                 // +0x24; xfer Int
	Int m_unk0x28;                                 // +0x28; xfer Int
protected:
	virtual void loadPostProcess() { UpdateModule::loadPostProcess(); }	// retail slot 1 0x00497805: a jmp to UpdateModule's
};
// SIZE 0x2C
typedef char ClickReactionBehavior_size[(sizeof(ClickReactionBehavior) == 0x2C) ? 1 : -1];
typedef char ClickReactionBehavior_off_m_unk0x24[(offsetof(ClickReactionBehavior, m_unk0x24) == 0x24) ? 1 : -1];
typedef char ClickReactionBehavior_off_m_unk0x28[(offsetof(ClickReactionBehavior, m_unk0x28) == 0x28) ? 1 : -1];

#endif
