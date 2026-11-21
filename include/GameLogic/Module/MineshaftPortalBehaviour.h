// MineshaftPortalBehaviour: the MineshaftPortalBehaviour update module. SIZE 0x3C: UpdateModule (0x20), a byte gap at
// +0x20 (interface table pointers and bytes xfer does not touch), then the two Bools that xfer (0x00373A0F) saves at
// +0x38 and +0x39. The constructor (0x00373096) runs UpdateModule's constructor and installs the tables. xfer also
// makes transfers this view cannot place: reads through slots 10, 4 and 8, a Char and an UnsignedInt at the
// misaligned +0x39.
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
	static Module *friend_newModuleInstance(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual UpdateSleepTime update();		// UpdateModuleInterface slot 0 (pure in UpdateModule)
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
