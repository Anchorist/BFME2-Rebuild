// FakePathfindPortalBehaviour.h: the FakePathfindPortalBehaviour module. SIZE 0x38 (ModuleFactory operator new).
// Target facts: the constructor 0x00461944 calls UpdateModule first; it stores the
// tables 0x00C1C780 at +0x20, 0x00C4EF80 at +0x24, 0x00C42C1C at +0x0, 0x00C42B60 at +0xC, 0x00C42B54 at +0x10, 0x00C42B50 at +0x20, 0x00C42B40 at +0x24. Members are what xfer (0x00461B1B) transfers after UpdateModule::xfer,
// typed by the Xfer slot each goes through, in that order; m_unk names are offsets
// (no map or donor name established). Bytes xfer does not touch are gaps.
// Not established: interface tables at +0x20, +0x24 (their vptrs sit in the gaps there).
// Not established: transfers xfer makes that this view cannot place: slot10 ?, slot4 ?, Char ?, slot4 ?.
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
