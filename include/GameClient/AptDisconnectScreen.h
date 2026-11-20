// AptDisconnectScreen.h: the multiplayer disconnect screen ("DisconnectScreen.apt").
//
// Target facts (retail game.dat, RVAs; table addresses are VAs):
//  - Constructor 0x00513558 (one argument for _bfme_AptGameWindow's constructor 0x0051268C), destructor 0x00512E49, tables VA
//    0x00865B6C (primary) and 0x00865B68 (AptCallbackHost secondary). SIZE 0x290 (screen factory 0x002D1EC9). The screen instance is
//    the global at VA 0x00E048D0 (the map names it TheDisconnectMenu).
//  - Members: +0x27C and +0x280 ints (the two gadgets InitGadgets 0x0051321A stores: the first is the "TextDisplay"-style window,
//    the second the entry the constructor registers), +0x284 a byte (OnInitialized sets it: a refresh is pending), +0x285 a byte,
//    +0x286..+0x28D eight bytes, one per player: whether the kick button is shown (rva00512CE9 invokes "ShowKickButton" or
//    "HideKickButton" with the player number and stores the flag; rva00512D47 reads it back).
#pragma once
#ifndef BFME2_APTDISCONNECTSCREEN_H
#define BFME2_APTDISCONNECTSCREEN_H

#include "GameClient/DisconnectMenu.h"
#include "Common/UnicodeString.h"

class GameWindow;

class AptDisconnectScreen : public DisconnectMenu
{
public:
	AptDisconnectScreen(void *);					// 0x00513558
	virtual ~AptDisconnectScreen();

	void OnInitialized(const char *);
	void InitGadgets(const char *, void *, GameWindow *);
	void SendChatLine(UnicodeString);				// 0x005130E2: filters the line and sends it as a disconnect chat message
	void OnBttnEnterText(const char *);
	virtual int rva00513449(int message, unsigned int data1, unsigned int data2);	// The screen's message handler (Enter in the chat entry sends the line)
	void rva00512CE9(int, bool);					// Shows or hides a player's kick button
	bool rva00512D47(int);							// The kick-button flag of a player
	void Quit(const char *);						// Announces that the local player left, drops every connection that is down and quits the game
	void Kick(const char *);						// Votes the player out through TheNetwork
	void PlayerColor(int, char *, bool);
	int rva00512DB1();								// Re-applies every kick button once

	void rva00513040(int, int);						// Sets a player's bar percent ("SetBarPercent")
	void rva00512EDD(int slot, UnicodeString name);	// Shows or clears a disconnected player
};
typedef char AptDisconnectScreenSizeCheck[sizeof(AptDisconnectScreen)==0x290 ? 1 : -1];

#endif
