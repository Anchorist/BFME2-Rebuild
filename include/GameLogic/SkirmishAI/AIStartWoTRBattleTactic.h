// Retail constructor 0x005AB1B4 calls Rva005DCC24 and installs table 0x00C72224.
#pragma once
#ifndef BFME2_AISTARTWOTRBATTLETACTIC_H
#define BFME2_AISTARTWOTRBATTLETACTIC_H

#include "GameLogic/SkirmishAI/AITacticKinds.h"

class Xfer;

class AIStartWoTRBattleTactic : public Rva005DCC24
{
public:
	AIStartWoTRBattleTactic();							// 0x005AB1B4
	virtual ~AIStartWoTRBattleTactic();					// (deleting form at slot 0)
	virtual Bool canRun(void *request);
	virtual void cleanUp() {} // native 0x000B3FD0
	virtual void xfer(Xfer *xfer);
	virtual unsigned int vslot04() { return 0; } // native 0x000D43D0
	virtual void run();
	virtual void update() {} // native 0x000B3FD0
	virtual AITactic *create();							// Slot 9
};
// SIZE 0x58 (no members of its own)
typedef char AIStartWoTRBattleTactic_size[(sizeof(AIStartWoTRBattleTactic) == 0x58) ? 1 : -1];

#endif
