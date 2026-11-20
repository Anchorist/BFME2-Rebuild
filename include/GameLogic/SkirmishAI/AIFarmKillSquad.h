// Retail constructor 0x005ACF38 calls Rva005DCC24 and installs table 0x00C72474.
#pragma once
#ifndef BFME2_AIFARMKILLSQUAD_H
#define BFME2_AIFARMKILLSQUAD_H

#include "GameLogic/SkirmishAI/AITacticKinds.h"

class Xfer;

class AIFarmKillSquad : public Rva005DCC24
{
public:
	AIFarmKillSquad();									// 0x005ACF38
	virtual ~AIFarmKillSquad();							// (row 11B)
	virtual Bool canRun(void *request);
	virtual void cleanUp();
	virtual Bool initializeTeamTemplate(void *team, Int count);
	virtual void xfer(Xfer *xfer);
	virtual void run() {} // native 0x000B3FD0
	virtual void update();
	virtual AITactic *create();							// Slot 9

	ObjectID m_targetID; // 0x005AD5DD saves the selected attack target ID
	ObjectID m_unk0x5C;									// +0x5C; likewise
	Bool m_unk0x60; // 0x005ACF38 initializes this byte to a predicate; 0x005ACFAB copies it
};
// SIZE 0x64
typedef char AIFarmKillSquad_size[(sizeof(AIFarmKillSquad) == 0x64) ? 1 : -1];

#endif
