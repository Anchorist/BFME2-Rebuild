// Retail constructor 0x005A9988 calls AITacticOffensive and installs table 0x00C71DB4.
#pragma once
#ifndef BFME2_AIBASEPENETRATIONTROOPSTACTIC_H
#define BFME2_AIBASEPENETRATIONTROOPSTACTIC_H

#include "GameLogic/SkirmishAI/AITacticKinds.h"

class AIBasePenetrationTroopsTactic : public AITacticOffensive
{
public:
	AIBasePenetrationTroopsTactic();					// 0x005A9988
	virtual ~AIBasePenetrationTroopsTactic();			// (row 11B)
	virtual Bool canRun(void *request);
	virtual void cleanUp();
	virtual Bool initializeTeamTemplate(void *team, Int count);
	virtual void run();
	virtual void update();
	virtual AITactic *create();							// Slot 9
};
// SIZE 0x58 (no members of its own)
typedef char AIBasePenetrationTroopsTactic_size[(sizeof(AIBasePenetrationTroopsTactic) == 0x58) ? 1 : -1];

#endif
