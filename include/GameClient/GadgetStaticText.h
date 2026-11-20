// GadgetStaticText.h: the static text gadget's free-function interface, declared from the
// names retail's own map carries (decorated names demangled; every one is a plain
// cdecl function that takes the window first). The per-gadget data struct lives in
// the window's instance data, so none of it is exposed here. Each
// declaration's comment is its retail RVA. Evidence: map identities only; the data
// layouts behind them are recovered with the functions that use them.
#pragma once
#ifndef BFME2_GADGETSTATICTEXT_H
#define BFME2_GADGETSTATICTEXT_H

#include "GameClient/GameWindow.h"

class DisplayString;

// The static text's user data (GameWindow::winGetUserData): the display string that draws the text (set by
// GadgetStaticTextSetFont 0x0032143D, read by GadgetStaticTextGetText 0x00321599) and the centering flag, which the
// script parser reads from the window block at 0x00315283.
struct _TextData
{
	DisplayString *m_text;	// +0x00
	bool m_centered;	// +0x04
};
typedef struct _TextData TextData;

class AsciiString;
class UnicodeString;
class GameFont;
class Image;

WindowMsgHandledType GadgetStaticTextInput(GameWindow *, unsigned int, unsigned int, unsigned int);	// 0x003213F0
void GadgetStaticTextSetFont(GameWindow *, GameFont *);	// 0x0032143D
WindowMsgHandledType GadgetStaticTextSystem(GameWindow *, unsigned int, unsigned int, unsigned int);	// 0x00321494
void GadgetStaticTextSetText(GameWindow *, UnicodeString);	// 0x00321552
UnicodeString GadgetStaticTextGetText(GameWindow *);	// 0x00321599

#endif
