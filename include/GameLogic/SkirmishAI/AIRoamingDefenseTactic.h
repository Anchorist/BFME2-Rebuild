// Retail constructor 0x005AABC6 calls Rva005DCC24 and installs table 0x00C720E8.
#pragma once
#ifndef BFME2_AIROAMINGDEFENSETACTIC_H
#define BFME2_AIROAMINGDEFENSETACTIC_H

#include "GameLogic/SkirmishAI/AITacticKinds.h"

class Xfer;

class AIRoamingDefenseTactic : public Rva005DCC24
{
public:
	AIRoamingDefenseTactic();							// 0x005AABC6
	virtual ~AIRoamingDefenseTactic();					// 0x005AAB91 (row 11B)
	virtual Bool canRun(void *request);					// 0x005AAC35
	virtual void cleanUp();								// 0x005AAD26
	virtual Bool initializeTeamTemplate(void *team, Int count);	// 0x005AADD9
	virtual void xfer(Xfer *xfer);						// 0x005AABA5
	virtual unsigned int vslot04() { return 0; } // native 0x000D43D0
	virtual void run();									// 0x005AAB9C
	virtual void update();								// 0x005AB085
	virtual AITactic *create();							// 0x005AADA7, slot 9

	bool m_flag58;										// +0x58; xfer 0x005AABA5 stores it through Xfer's bool operator
	unsigned char m_unk0x59[3];							// +0x59..+0x5C: not shown
};
// SIZE 0x5C
typedef char AIRoamingDefenseTactic_size[(sizeof(AIRoamingDefenseTactic) == 0x5C) ? 1 : -1];
typedef char AIRoamingDefenseTactic_off_m_flag58[(offsetof(AIRoamingDefenseTactic, m_flag58) == 0x58) ? 1 : -1];

#endif
