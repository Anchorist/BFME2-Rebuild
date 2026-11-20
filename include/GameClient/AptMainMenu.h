// AptMainMenu.h: the main menu screen ("MainMenu.apt").
//
// Target facts (retail game.dat, RVAs; table addresses are VAs):
//  - Constructor 0x00516211 (one argument for _bfme_AptGameWindow's constructor 0x0051268C), destructor 0x00514EAB, deleting
//    destructor 0x0051588B; tables VA 0x00865F10 (primary) and 0x00865F0C (AptCallbackHost secondary). SIZE 0x2AC (screen
//    factory 0x002D1FB1).
//  - Members: +0x27C..+0x282 seven flag bytes (zeroed by the constructor), +0x288 the pending action (the constructor stores
//    8 or 0, from a flag in the global at VA 0x00DFE77C) and +0x28C its argument, a 0x14-byte object at +0x290 (constructor
//    0x005B6ED1), +0x2A4 an int, +0x2A8 a byte ('E' at construction; the campaign handlers copy their argument's first
//    character into it).
//  - The button handlers store the pending action: LoadGame, Options, CreateAHero, WarOfTheRing, LoadCampaign, Skirmish, LoadReplay,
//    GoodCampaign and EvilCampaign set +0x288 to 9 and +0x28C to the kind (1, 4/5, 9, 8, 2, 7, 3, 0xB, 0xC); 0x00514B8D, 0x00514BA1
//    and 0x00514BB5 set +0x288 to 5, 6 and 7 while the menu instance (the map's g_Va00E048DC) exists.
#pragma once
#ifndef BFME2_APTMAINMENU_H
#define BFME2_APTMAINMENU_H

#include "GameClient/BfmeAptGameWindow.h"
#include "Common/AsciiString.h"

class AptMainMenu : public _bfme_AptGameWindow
{
public:
	AptMainMenu(void *);							// 0x00516211
	virtual ~AptMainMenu();

	virtual int rva00514950(int, int, int);

	static int LinearCampaignStart(const AsciiString &campaign, float time, bool restart);

	void LoadGame(const char *);
	void Options(const char *);
	void GoodCampaign(const char *);
	void EvilCampaign(const char *);
	void CreateAHero(const char *);
	void WarOfTheRing(const char *);
	void LoadCampaign(const char *);
	void rva00514B8D();
	void rva00514BA1();
	void rva00514BB5();
	void Skirmish(const char *);
	void LoadReplay(const char *);
	void StopGameMovie(const char *);
	void ContinueCampaign(const char *);			// Stays on the menu when the campaign autosave exists
	void BattleSchool(const char *);
	void ResetResolution(const char *);
	void RenderCredits(void *, void *, void *, void *);
	void rva00514DC0(int);
	void rva00514878();								// Cancels a pending action 2 and turns the shell map back on
	void rva00514FE9();								// The tutorial prompt's close: restores the shell's music and reverses the MainMenuToSubMenu transition
	void rva00515633();
	void ShowCreditsMenu();							// 0x005158A7: picks the credits menu and runs rva00515633
	void OnInitialized(const char *);

	bool m_flag27C;									// +0x27C (OnInitialized sets it)
	bool m_flag27D;									// +0x27D
	bool m_flag27E;									// +0x27E
	bool m_flag27F;									// +0x27F
	bool m_flag280;									// +0x280
	bool m_flag281;									// +0x281
	bool m_flag282;									// +0x282 (0x00514DC0: set when the action is 8 and the argument is 2)
	unsigned char m_pad283[5];
	int m_action;									// +0x288
	int m_actionArg;								// +0x28C
	unsigned char m_x290[0x14];						// +0x290: an object built by 0x005B6ED1
	AsciiString m_menuName;							// +0x2A4 (ShowCreditsMenu 0x005158A7 sets "CreditsMenu")
	char m_campaignInitial;							// +0x2A8
	unsigned char m_pad2A9[3];
};
typedef char AptMainMenuSizeCheck[sizeof(AptMainMenu)==0x2AC ? 1 : -1];

#endif
