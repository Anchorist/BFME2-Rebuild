// cl: /O1
// Portions derived from Command & Conquer Generals and Command & Conquer Generals Zero Hour, (c) Electronic Arts Inc., GPL-3.0-or-later; see LICENSE and NOTICE.
#include "GameClient/GadgetStaticText.h"
#include "GameClient/GadgetProgressBar.h"
#include "GameClient/GameWindowManager.h"
#include "GameClient/WinInstanceData.h"
#include "GameClient/DisplayString.h"
#include "GameClient/DisplayStringManager.h"
#include "Common/UnicodeString.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G003213F0 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x003213F0 size=77 name=?GadgetStaticTextInput@@YA?AW4WindowMsgHandledType@@PAVGameWindow@@III@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0032143D size=87 name=?GadgetStaticTextSetFont@@YAXPAVGameWindow@@PAVGameFont@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void GadgetStaticTextSetFont(GameWindow *window, GameFont *font)
{
	TextData *textData = (TextData *)window->winGetUserData();
	DisplayString *displayString;

	// The window's own text and tooltip strings, then the static text's.
	displayString = window->winGetInstanceData()->getTextDisplayString();
	if (displayString)
		displayString->setFont(font);
	displayString = window->winGetInstanceData()->getTooltipDisplayString();
	if (displayString)
		displayString->setFont(font);

	if (textData)
	{
		displayString = textData->m_text;
		if (displayString)
			displayString->setFont(font);
	}
}
// FUNCTION: BFME2 0x00321494 size=190 name=?GadgetStaticTextSystem@@YA?AW4WindowMsgHandledType@@PAVGameWindow@@III@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
WindowMsgHandledType GadgetStaticTextSystem(GameWindow *window, UnsignedInt msg, UnsignedInt mData1, UnsignedInt mData2)
{
	switch (msg)
	{
		case 0x4001:
			if (mData1)
			{
				TextData *tData = (TextData *)window->winGetUserData();
				if (tData && tData->m_text)
					tData->m_text->setText(*(UnicodeString *)mData1);
			}
			break;
		case 0x4002:
		{
			TextData *tData = (TextData *)window->winGetUserData();
			if (tData && tData->m_text)
				*(UnicodeString *)mData2 = tData->m_text->getText();
			break;
		}
		case 1:
			break;
		case 2:
		{
			TextData *tData = (TextData *)window->winGetUserData();
			TheDisplayStringManager->freeDisplayString(tData->m_text);
			delete tData;
			break;
		}
		default:
			return MSG_IGNORED;
	}
	return MSG_HANDLED;
}
// FUNCTION: BFME2 0x00321552 size=71 name=?GadgetStaticTextSetText@@YAXPAVGameWindow@@VUnicodeString@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void GadgetStaticTextSetText(GameWindow *window, UnicodeString text)
{
	if (!window)
		return;
	TheWindowManager->winSendSystemMsg(window, 0x4001, (unsigned int)&text, 0);
}
// FUNCTION: BFME2 0x00321599 size=54 name=?GadgetStaticTextGetText@@YA?AVUnicodeString@@PAVGameWindow@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
UnicodeString GadgetStaticTextGetText(GameWindow *window)
{
	if (!window)
		return UnicodeString::TheEmptyString;
	TextData *textData = (TextData *)window->winGetUserData();
	if (!textData)
		return UnicodeString::TheEmptyString;
	return textData->m_text->getText();
}
// FUNCTION: BFME2 0x003215CF size=44 name=?GadgetProgressBarSystem@@YA?AW4WindowMsgHandledType@@PAVGameWindow@@III@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
WindowMsgHandledType GadgetProgressBarSystem(GameWindow *window, UnsignedInt msg, UnsignedInt mData1, UnsignedInt mData2)
{
	switch (msg)
	{
		case 0x4033:
			if ((Int)mData1 >= 0 && (Int)mData1 <= 100)
				window->winSetUserData((void *)mData1);
			return MSG_HANDLED;
		default:
			return MSG_IGNORED;
	}
}
// FUNCTION: BFME2 0x003215FB size=37 name=?GadgetProgressBarSetProgress@@YAXPAVGameWindow@@H@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void GadgetProgressBarSetProgress(GameWindow *window, Int progress)
{
	if (!window)
		return;
	TheWindowManager->winSendSystemMsg(window, 0x4033, progress, 0);
}
// FUNCTION: BFME2 0x00321620 size=656 name=?GadgetVerticalSliderInput@@YA?AW4WindowMsgHandledType@@PAVGameWindow@@III@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x003218B0 size=672 name=?GadgetVerticalSliderSystem@@YA?AW4WindowMsgHandledType@@PAVGameWindow@@III@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00321B50 size=780 name=?GadgetHorizontalSliderInput@@YA?AW4WindowMsgHandledType@@PAVGameWindow@@III@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00321E5C size=779 name=?GadgetHorizontalSliderSystem@@YA?AW4WindowMsgHandledType@@PAVGameWindow@@III@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
