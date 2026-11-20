// The victory conditions interface extends SubsystemInterface. Its native
// ctor 0x0041FDF8 initializes the mask at +0xC and installs the 31-slot table
// at 0x0083B988. The concrete class installs 0x0083BA28 and adds slot 31.
// The factory at 0x00420353 allocates 0x94 bytes.
#pragma once

#include "Common/SubsystemInterface.h"

class Player;

class VictoryConditionsInterface : public SubsystemInterface
{
public:
	VictoryConditionsInterface();							// 0x0041FDF8
	virtual ~VictoryConditionsInterface();					// 0x0041FE0E

	virtual Bool hasAchievedVictory(Player *player) = 0;
	virtual Bool hasBeenDefeated(Player *player) = 0;
	virtual Bool hasSinglePlayerBeenDefeated(Player *player) = 0;
	virtual void cachePlayerPtrs() = 0;
	virtual Bool isLocalAlliedVictory() = 0;
	virtual Bool isLocalAlliedDefeat() = 0;
	virtual Bool isLocalDefeat() = 0;
	virtual Bool amIObserver() const = 0;
	virtual UnsignedInt getEndFrame() const = 0;
	virtual void showEndGame(const AsciiString &label, Bool defeat, const AsciiString &name, const AsciiString &extra) = 0;
	virtual void hideEndGame() = 0;
	virtual Bool isPlayerDefeated(Int slot) const = 0;
	virtual Bool cachePlayerPtr(Player *player) = 0;
	virtual void setForceSinglePlayerDefeat(Bool force) = 0;
	virtual void rva004201ED(Bool value) = 0;
	virtual Bool getForceSinglePlayerDefeat() const = 0;
	virtual Bool rva00094AE3() const = 0;

protected:
	Int m_victoryConditions;								// +0xC, reset selects this mask from the game type.
};

class VictoryConditions : public VictoryConditionsInterface
{
public:
	VictoryConditions();									// 0x0042017F
	virtual ~VictoryConditions();
	virtual void init() { reset(); }						// 0x000D20D6 forwards through slot 9.
	virtual void reset();									// 0x0041FE86
	virtual void update();

	virtual Bool hasAchievedVictory(Player *player);
	virtual Bool hasBeenDefeated(Player *player);
	virtual Bool hasSinglePlayerBeenDefeated(Player *player);
	virtual void cachePlayerPtrs();
	virtual Bool isLocalAlliedVictory();
	virtual Bool isLocalAlliedDefeat();
	virtual Bool isLocalDefeat();							// 0x004200FD, observer guard plus local defeat flag.
	virtual Bool amIObserver() const;						// 0x004201CE, reads +0x86.
	virtual UnsignedInt getEndFrame() const;				// 0x0036750C, reads +0x6C.
	virtual void showEndGame(const AsciiString &label, Bool defeat, const AsciiString &name, const AsciiString &extra);	// 0x00420254
	virtual void hideEndGame();								// 0x00420110
	virtual Bool isPlayerDefeated(Int slot) const;			// 0x004201D5
	virtual Bool cachePlayerPtr(Player *player);				// 0x00420017
	virtual void setForceSinglePlayerDefeat(Bool force);		// 0x004201E0
	virtual void rva004201ED(Bool value);						// Sets +0x91.
	virtual Bool getForceSinglePlayerDefeat() const;			// 0x00094ADC, reads +0x90.
	virtual Bool rva00094AE3() const;							// Reads +0x91.
	virtual void updateEndGameDisplay();					// 0x0041FE63 hides the timed-out display.

	Bool testDefeat(Player *player);

private:
	Bool m_endGameShowing;									// +0x10, showEndGame sets it and hideEndGame clears it.
	UnsignedInt m_endGameShowTime;							// +0x14, 0x0041FE63 compares it with timeGetTime().
	Player *m_players[20];									// +0x18
	Int m_localSlotNum;										// +0x68
	UnsignedInt m_endFrame;									// +0x6C
	Bool m_isDefeated[20];									// +0x70
	Bool m_localPlayerDefeated;								// +0x84
	Bool m_singleAllianceRemaining;							// +0x85
	Bool m_isObserver;										// +0x86
	Int m_defeatedPlayerCount;								// +0x88, incremented by hasSinglePlayerBeenDefeated.
	Int m_cachedPlayerCount;								// +0x8C, 0x00420017 appends a player then increments it.
	Bool m_forceSinglePlayerDefeat;							// +0x90, the early true result at 0x0042090C.
	Bool m_unk0x91;
};

typedef char VictoryConditionsInterfaceSize[(sizeof(VictoryConditionsInterface) == 0x10) ? 1 : -1];
typedef char VictoryConditionsSize[(sizeof(VictoryConditions) == 0x94) ? 1 : -1];

extern VictoryConditions *TheVictoryConditions;				// 0x00E03138

