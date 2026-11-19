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
	virtual ~AIFlankAttackTactic();						// 0x005AA55D
	virtual Bool canRun(void *request);					// 0x005AA0D8
	virtual void cleanUp() {} // native 0x000B3FD0
	virtual void xfer(Xfer *xfer);						// 0x005AA60F
	virtual void run();									// 0x005AA5AE
	virtual void update();								// 0x005AA1EA
	virtual AITactic *create();							// 0x005AA2A7, slot 9

	AIFlankAttackTacticImp *m_impl;						// +0x58
};
// SIZE 0x5C
typedef char AIFlankAttackTactic_size[(sizeof(AIFlankAttackTactic) == 0x5C) ? 1 : -1];
typedef char AIFlankAttackTactic_off_m_impl[(offsetof(AIFlankAttackTactic, m_impl) == 0x58) ? 1 : -1];

#endif
