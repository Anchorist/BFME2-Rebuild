// Retail constructor 0x005AC7EC calls Rva005DCC24 and installs table 0x00C723E8.
#pragma once
#ifndef BFME2_AIRINGHEROTACTIC_H
#define BFME2_AIRINGHEROTACTIC_H

#include "GameLogic/SkirmishAI/AITacticKinds.h"

class AIRingHeroTactic : public Rva005DCC24
{
public:
	AIRingHeroTactic();									// 0x005AC7EC
	virtual Bool canRun(void *request);					// the base pure slots the class overrides (rows not written)
	virtual void cleanUp();
	virtual Bool initializeTeamTemplate(void *team, Int count);
	virtual unsigned int vslot04() { return 0; } // native 0x000D43D0
	virtual void run();
	virtual void update();
	virtual ~AIRingHeroTactic();
	virtual AITactic *create();							// 0x005AC8F2, slot 9

	ObjectID m_unk0x58; // resolved through GameLogic::findObjectByID in 0x005ACBFF
	UnsignedInt m_unk0x5C;
	Bool m_unk0x60; // byte flag set when the requested action is recorded in 0x005ACBFF
	UnsignedInt m_unk0x64;
};
// SIZE 0x68
typedef char AIRingHeroTactic_size[(sizeof(AIRingHeroTactic) == 0x68) ? 1 : -1];

#endif
