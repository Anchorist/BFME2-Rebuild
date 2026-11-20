// Retail constructor 0x005AA23E calls AITacticOffensive and installs table 0x00C71EB0.
#pragma once
#ifndef BFME2_AIFLANKATTACKTACTIC_H
#define BFME2_AIFLANKATTACKTACTIC_H

#include "GameLogic/SkirmishAI/AITacticKinds.h"
#include "GameLogic/SkirmishAI/AIFlankAttackTacticImp.h"

class Xfer;

class AIFlankAttackTactic : public AITacticOffensive
{
public:
	AIFlankAttackTactic();								// 0x005AA23E
	virtual ~AIFlankAttackTactic();
	virtual Bool canRun(void *request);
	virtual void cleanUp() {} // native 0x000B3FD0
	virtual void xfer(Xfer *xfer);
	virtual void run();
	virtual void update();
	virtual AITactic *create();							// Slot 9

	AIFlankAttackTacticImp *m_impl;						// +0x58
};
// SIZE 0x5C
typedef char AIFlankAttackTactic_size[(sizeof(AIFlankAttackTactic) == 0x5C) ? 1 : -1];
typedef char AIFlankAttackTactic_off_m_impl[(offsetof(AIFlankAttackTactic, m_impl) == 0x58) ? 1 : -1];

#endif
