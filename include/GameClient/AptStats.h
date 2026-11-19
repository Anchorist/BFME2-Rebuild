// Apt controls for the persistent faction statistics table.
#pragma once

#include "GameClient/GameStats.h"

class AptStats : public GameStats::Persistent
{
public:
	AptStats(void *callbackOwner);
	virtual ~AptStats();

	virtual void statsSlot1() = 0;
	virtual void statsSlot2() = 0;
	virtual void statsSlot3();
	virtual void InitGadgets();

	void rva005DD1D0(const char *text);
	void rva005DD0EB(int tab);
	void ColorExtern(int index, char *text, bool query);

private:
	void *m_callbackOwner;
	Int m_selectedTab;
	std::vector<Int> m_factionIndices;
};

typedef char AptStatsSizeCheck[sizeof(AptStats) == 0x2C ? 1 : -1];
