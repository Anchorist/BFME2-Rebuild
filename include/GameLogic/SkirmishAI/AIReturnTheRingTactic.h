// Retail constructor 0x005AB3BE calls Rva005DCC24 and installs table 0x00C72284.
#pragma once
#ifndef BFME2_AIRETURNTHERINGTACTIC_H
#define BFME2_AIRETURNTHERINGTACTIC_H

#include "GameLogic/SkirmishAI/AITacticKinds.h"

class Xfer;

class AIReturnTheRingTactic : public Rva005DCC24
{
public:
	AIReturnTheRingTactic();							// 0x005AB3BE
	virtual ~AIReturnTheRingTactic();					// 0x005AB309 (row 11B)
	virtual Bool canRun(void *request);					// 0x005AB6A5
	virtual void cleanUp();								// 0x005AB314
	virtual void xfer(Xfer *xfer);						// 0x005AB354
	virtual unsigned int vslot04() { return m_unk0x58; } // native 0x003F3FCE
	virtual void run();									// 0x005AB751
	virtual void update();								// 0x005AB71D
	Bool garrisonFortress();						// 0x005AB66A
	virtual AITactic *create();							// 0x005AB41F, slot 9
	virtual Bool vslot10() const { return true; } // native 0x0050B5C6

	UnsignedInt m_unk0x58;								// +0x58; xfer 0x005AB354 writes it through the unsigned int operator
	ObjectID m_ringBearerID; // 0x005AB45B stores it and 0x005AB4B9 resolves it
	ObjectID m_fortressID; // set by 0x005AB6DC and resolved by 0x005AB66A
	Bool m_garrisonAttempted; // 0x005AB71D sets after garrisonFortress (0x005AB66A)
	Bool m_flag65;										// +0x65; likewise
	unsigned char m_unk0x66[0x2];						// +0x66..+0x68: not shown
};
// SIZE 0x68
typedef char AIReturnTheRingTactic_size[(sizeof(AIReturnTheRingTactic) == 0x68) ? 1 : -1];

#endif
