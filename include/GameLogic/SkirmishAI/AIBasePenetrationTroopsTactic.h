// Retail constructor 0x005A9988 calls AITacticOffensive and installs table 0x00C71DB4.
#pragma once
#ifndef BFME2_AIBASEPENETRATIONTROOPSTACTIC_H
#define BFME2_AIBASEPENETRATIONTROOPSTACTIC_H

#include "GameLogic/SkirmishAI/AITacticKinds.h"

class AIBasePenetrationTroopsTactic : public AITacticOffensive
{
public:
	AIBasePenetrationTroopsTactic();					// 0x005A9988
	virtual ~AIBasePenetrationTroopsTactic();			// 0x005A990B (row 11B)
	virtual Bool canRun(void *request);					// 0x005A99D7
	virtual void cleanUp();								// 0x005A994B
	virtual Bool initializeTeamTemplate(void *team, Int count);
	virtual void run();									// 0x005A9916
	virtual void update();								// 0x005A9923
	virtual AITactic *create();							// 0x005A9A57, slot 9
};
// SIZE 0x58 (no members of its own)
typedef char AIBasePenetrationTroopsTactic_size[(sizeof(AIBasePenetrationTroopsTactic) == 0x58) ? 1 : -1];

#endif
