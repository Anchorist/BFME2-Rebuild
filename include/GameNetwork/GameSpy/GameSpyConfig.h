// GameSpyConfig.h: the interface to the GameSpy configuration object (Zero Hour's GameSpyConfigInterface by role and slot order,
// GPL-3.0-or-later; the slot numbers and the global are retail's).
// Portions derived from Command & Conquer Generals Zero Hour, (c) Electronic Arts Inc., GPL-3.0-or-later; see LICENSE and NOTICE.
// Target facts (code RVAs, global VA 0x00E05FB4 = RVA 0x00A05FB4):
//  - SetUpGameSpy 0x00386F7F stores the object GameSpyConfigInterface::create 0x0054F4AF builds in the global and TearDownGameSpy
//    0x00385956 clears it.
//  - The base interface vtable (0x0086A894) has 14 slots (0..13, ending at restrictGamesToLobby); GameSpyConfig adds the 6 NAT
//    timeout getters at slots 14..19.
#pragma once
#ifndef BFME2_GAMESPYCONFIG_H
#define BFME2_GAMESPYCONFIG_H

#include <list>
#include "Common/GameType.h"
#include "Common/AsciiString.h"

class GameSpyConfigInterface
{
public:
	virtual ~GameSpyConfigInterface() {}											// slot 0x00
	virtual _STL::list<AsciiString> getPingServers() = 0;							// slot 0x04
	virtual Int getNumPingRepetitions() = 0;										// slot 0x08
	virtual Int getPingTimeoutInMs() = 0;											// slot 0x0C
	virtual Int getPingCutoffGood() = 0;											// slot 0x10
	virtual Int getPingCutoffBad() = 0;												// slot 0x14
	virtual _STL::list<AsciiString> getQMMaps() = 0;								// slot 0x18
	virtual Int getQMBotID() = 0;													// slot 0x1C
	virtual Int getQMChannel() = 0;													// slot 0x20
	virtual void setQMChannel(Int channel) = 0;										// slot 0x24
	virtual Bool isPlayerVIP(Int id) = 0;											// slot 0x28
	virtual Bool getManglerLocation(Int index, AsciiString &host, UnsignedShort &port) = 0;	// slot 0x2C
	virtual AsciiString getLeftoverConfig() = 0;									// slot 0x30
	virtual Bool restrictGamesToLobby() = 0;										// slot 0x34

	static GameSpyConfigInterface *create(AsciiString config);
};

extern GameSpyConfigInterface *TheGameSpyConfig;

#endif
