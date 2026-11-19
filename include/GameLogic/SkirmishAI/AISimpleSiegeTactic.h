// Retail constructor 0x005A9D33 calls AITacticSiege and installs table 0x00C71E6C.
#pragma once
#ifndef BFME2_A_I_SIMPLE_SIEGE_TACTIC_H
#define BFME2_A_I_SIMPLE_SIEGE_TACTIC_H

#include "GameLogic/SkirmishAI/AITacticKinds.h"

class AISimpleSiegeTactic : public AITacticSiege
{
public:
	AISimpleSiegeTactic();
	virtual ~AISimpleSiegeTactic();
	virtual AITactic *create();
	virtual Bool canRun(void *request);	// the base pure slots the class overrides (rows not written)
	virtual void cleanUp() { m_unk0x5C = 0; } // native 0x005A9D01
	virtual Bool initializeTeamTemplate(void *team, Int count);
	virtual void xfer(Xfer *xfer);
	virtual unsigned int vslot04() { return 2; } // native 0x0022C4CB
	virtual void run() { m_unk0x5C = 0; } // native 0x005A9D01
	virtual void update();

	UnsignedInt m_unk0x5C; // cleared by 0x005A9D01; xfer 0x005A9D06 reads and restores it
};
// SIZE 0x60
typedef char AISimpleSiegeTactic_size[(sizeof(AISimpleSiegeTactic) == 0x60) ? 1 : -1];

#endif
