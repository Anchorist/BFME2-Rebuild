// FakePathfindPortalBehaviour: the FakePathfindPortalBehaviour update module. SIZE 0x38: UpdateModule (0x20), two
// interface table pointers and other bytes xfer does not touch (byte gap at +0x20), then the three Bools that xfer
// (0x00461B1B) saves at +0x30..+0x32. The constructor (0x00461944) runs UpdateModule's constructor and installs the
// tables. xfer also makes transfers this view cannot place: two reads through slot 10 and two through slot 4, and a
// Char.
#pragma once
#ifndef BFME2_FAKE_PATHFIND_PORTAL_BEHAVIOUR_H
#define BFME2_FAKE_PATHFIND_PORTAL_BEHAVIOUR_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/UpdateModule.h"

class Thing;
class ModuleData;
class Xfer;

// UpdateModule ends at 0x20; this class's members follow it.
typedef char FakePathfindPortalBehaviour_base_size[(sizeof(UpdateModule) == 0x20) ? 1 : -1];

class FakePathfindPortalBehaviour : public UpdateModule
{
public:
	FakePathfindPortalBehaviour(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual ~FakePathfindPortalBehaviour();
	virtual UpdateSleepTime update();	// override: update slot 0 at +0x10 (0x00461DC7)

protected:
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

public:
	UnsignedByte m_gap0x20[0x10];
	Bool m_unk0x30;                                // +0x30; xfer Bool
	Bool m_unk0x31;                                // +0x31; xfer Bool
	Bool m_unk0x32;                                // +0x32; xfer Bool
	UnsignedByte m_gap0x33[0x5];
protected:
	virtual void loadPostProcess() { UpdateModule::loadPostProcess(); }	// retail slot 1 0x00497805: a jmp to UpdateModule's
};
// SIZE 0x38
typedef char FakePathfindPortalBehaviour_size[(sizeof(FakePathfindPortalBehaviour) == 0x38) ? 1 : -1];
typedef char FakePathfindPortalBehaviour_off_m_unk0x30[(offsetof(FakePathfindPortalBehaviour, m_unk0x30) == 0x30) ? 1 : -1];
typedef char FakePathfindPortalBehaviour_off_m_unk0x31[(offsetof(FakePathfindPortalBehaviour, m_unk0x31) == 0x31) ? 1 : -1];
typedef char FakePathfindPortalBehaviour_off_m_unk0x32[(offsetof(FakePathfindPortalBehaviour, m_unk0x32) == 0x32) ? 1 : -1];

#endif
