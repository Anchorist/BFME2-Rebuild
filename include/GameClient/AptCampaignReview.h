// AptCampaignReview.h: the campaign review screen ("CampaignReview.apt"). It adds no members to _bfme_AptGameWindow.
//
// Target facts (retail game.dat, RVAs; table addresses are VAs): constructor 0x00512AC8 (one argument for the base constructor
// 0x0051268C), destructor 0x00512894; SIZE 0x27C (screen factory 0x002D1E8F allocates exactly the base's size). The screen instance is the
// global the map names g_obj12F495C (VA 0x00E048C8, typed void*).
#pragma once
#ifndef BFME2_APTCAMPAIGNREVIEW_H
#define BFME2_APTCAMPAIGNREVIEW_H

#include "GameClient/BfmeAptGameWindow.h"

class AptCampaignReview : public _bfme_AptGameWindow
{
public:
	AptCampaignReview(void *);						// 0x00512AC8
	virtual ~AptCampaignReview();

	void Continue(const char *);
	void TotalCampaignScore(int, char *, bool);		// Extern handler, prints the campaign score with "%d"
	void playerSideType(int, char *, bool);			// Extern handler, "evil" or "good"
	void DisplayVictoryLevel();						// Sets the APT:CmpgnRevResult text
	virtual WindowMsgHandledType system(unsigned int message, unsigned int data1, unsigned int data2);	// GameWindow slot 2, 0x005127F3
	virtual GameWindowFactory getWindowFactory();	// GameWindow slot 7, 0x00512C82
	static bool OpenScreen();
};
typedef char AptCampaignReviewSizeCheck[sizeof(AptCampaignReview)==0x27C ? 1 : -1];

#endif
