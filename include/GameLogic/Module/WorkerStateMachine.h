// WorkerAIUpdate::createMachines (0x004A9ED5) allocates 0x3C bytes.
// The 0x004A9964 destructor restores this table and tail-calls ~StateMachine.
// Table slots 2 and 3 are the snapshot name and the shared version-only xfer.
#pragma once
#include "Common/StateMachine.h"
#include "Common/Xfer.h"

class WorkerStateMachine : public StateMachine
{
public:
	// The transition tests the machine's states use to decide when the supply-truck sub-machine runs.
	static bool supplyTruckSubMachineWantsToEnter(State *state, void *userData);
	static bool supplyTruckSubMachineReadyToLeave(State *state, void *userData);
	WorkerStateMachine(Object *owner); // 0x004A9D79 (the map's COMDAT constructor)
	virtual ~WorkerStateMachine(); // (deleting 0x004A9E22)
protected:
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer) { StateMachine::xfer(xfer); xfer->Version1(); }	// slot 3: the shared version-only override 0x0033FB0B
};
// SIZE 0x3C
typedef char WorkerStateMachine_size[(sizeof(WorkerStateMachine) == 0x3C) ? 1 : -1];
