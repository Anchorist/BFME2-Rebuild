// The Apt spell store shares the ordinary Apt game-window base.
// Retail 0x43DA1B allocates 0x35C, and 0x43D686 installs its two leaf tables.
#pragma once

#include <stddef.h>
#include "Common/Vector.h"
#include "GameClient/BfmeAptGameWindow.h"

class CommandButton;
class CreateAHeroData;
enum ScienceType;

class AptSpellStore : public _bfme_AptGameWindow
{
public:
	explicit AptSpellStore(void *window);
	virtual ~AptSpellStore();

	virtual WindowMsgHandledType input(unsigned int message, unsigned int key, unsigned int flags);
	virtual WindowMsgHandledType system(unsigned int message, unsigned int data1, unsigned int data2);
	virtual int invokeCallback() { return 1; }  // primary slot 5, 0x910FB
	virtual GameWindowFactory getWindowFactory();
	virtual bool supportsWindowRenderer() { return true; }  // primary slot 10, 0x50B5C6
	virtual bool slot11() { return true; }  // primary slot 11, 0x50B5C6
	virtual void slot12() {}  // primary slot 12, 0xB3FD0
	virtual void slot13() {}  // primary slot 13, 0xB3FD0

	void OnInitialized(const char *name);
	void OnRollOverBttnSpell(const char *name);
	void OnRollOutBttnSpell(const char *name);
	void OnClosed(const char *name);
	void OnBttnSpell(const char *name);

	class PurchaseState
	{
	public:
		PurchaseState();
		~PurchaseState();

		virtual bool canBuy(ScienceType science);
		virtual int getPoints();
		virtual void updateFromHero(CreateAHeroData *hero, bool *available);

		int m_unk0x04;
		_STL::vector<ScienceType> m_pendingScience;
		int m_pendingCost;
	};

	_STL::vector<const CommandButton *> m_selectedSpells;
	PurchaseState m_purchaseState;
	bool m_unk0x2A0;
	bool m_unk0x2A1;
	bool m_unk0x2A2;
	bool m_unk0x2A3;
	int m_unk0x2A4;
	unsigned char m_unrecovered2A8[0xA0];  // twenty records of eight bytes each
	int m_unk0x348[4];
	bool m_unk0x358;
	bool m_unk0x359;
};

typedef char AptSpellStoreSizeCheck[sizeof(AptSpellStore) == 0x35C ? 1 : -1];
typedef char AptSpellStorePurchaseSizeCheck[sizeof(AptSpellStore::PurchaseState) == 0x18 ? 1 : -1];
typedef char AptSpellStorePurchaseOffset[offsetof(AptSpellStore, m_purchaseState) == 0x288 ? 1 : -1];
