// Retail constructor 0x005AB91D calls Rva005DCC24 and installs table 0x00C722EC.
#pragma once
#ifndef BFME2_AISTRUCTURECREEPTACTIC_H
#define BFME2_AISTRUCTURECREEPTACTIC_H

#include "GameLogic/SkirmishAI/AITacticKinds.h"

class Rva00573B23;

class AIStructureCreepTactic : public Rva005DCC24
{
public:
	AIStructureCreepTactic();							// 0x005AB91D
	virtual Bool canRun(void *request);			// the base pure slots the class overrides (rows not written)
	virtual void cleanUp();
	virtual void xfer(Xfer *xfer);
	virtual unsigned int vslot04() { return m_unk0x5C; } // native 0x0008BB81
	virtual void run();
	virtual void update();
	virtual ~AIStructureCreepTactic();
	virtual AITactic *create();							// 0x005AB9AF, slot 9

	ObjectID m_unk0x58; // 0x005AB843 transfers it through XferObjectID
	UnsignedInt m_unk0x5C;
	Rva00573B23 *m_buildRequest; // xfer load constructs this request via 0x00573A9B
	UnsignedInt m_unk0x64;
	UnsignedInt m_unk0x68;						// +0x68: create (0x005AB9AF) copies the creator's dword here after the constructor
	unsigned char m_unk0x6C[0x14];					// +0x6C..+0x80: not shown
};
// SIZE 0x80
typedef char AIStructureCreepTactic_size[(sizeof(AIStructureCreepTactic) == 0x80) ? 1 : -1];

#endif
