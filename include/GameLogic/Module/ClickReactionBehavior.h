// ClickReactionBehavior: the ClickReactionBehavior update module. SIZE 0x2C: UpdateModule (0x20), four
// bytes at +0x20 that hold an interface table pointer (not recovered), and the two Ints at +0x24 and +0x28 that xfer
// (0x00459579) saves after the base's data. The constructor (0x0045961D) runs UpdateModule's constructor and installs
// the tables.
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
	static Module *friend_newModuleInstance(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual UpdateSleepTime update();		// UpdateModuleInterface slot 0 (pure in UpdateModule)
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
