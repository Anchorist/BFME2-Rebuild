// Retail constructor 0x005AA9DB calls Rva005DCBE3 and installs table 0x00C71FF4.
#pragma once
#ifndef BFME2_AISIMPLEEXPANSIONTACTIC_H
#define BFME2_AISIMPLEEXPANSIONTACTIC_H

#include "GameLogic/SkirmishAI/AITacticKinds.h"

class Xfer;

class Rva00573B23;

class AISimpleExpansionTactic : public Rva005DCBE3
{
public:
	AISimpleExpansionTactic();							// 0x005AA9DB
	virtual ~AISimpleExpansionTactic();					// 0x005AA860 (row 11B)
	virtual Bool canRun(void *request);					// not written yet
	virtual void cleanUp();								// 0x005AA88D
	virtual void xfer(Xfer *xfer);						// 0x005AA90D
	virtual Bool initializeTeamTemplate(void *team, Int count);
	virtual void run() {} // native 0x000B3FD0
	virtual void update();								// 0x005AAB08
	virtual AITactic *create();							// 0x005AAAD6, slot 9

	Rva00573B23 *m_buildRequest; // xfer load constructs this request via 0x00573A9B
	UnsignedInt m_constructionState; // 0x005AAB08 advances this state through construction
};
// SIZE 0x60
typedef char AISimpleExpansionTactic_size[(sizeof(AISimpleExpansionTactic) == 0x60) ? 1 : -1];

#endif
