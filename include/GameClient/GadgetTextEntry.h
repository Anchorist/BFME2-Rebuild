// GadgetTextEntry.h: the text entry gadget's free-function interface, declared from the
// names retail's own map carries (decorated names demangled; every one is a plain
// cdecl function that takes the window first). The per-gadget data struct lives in
// the window's instance data, so none of it is exposed here. Each
// declaration's comment is its retail RVA. Evidence: map identities only; the data
// layouts behind them are recovered with the functions that use them.
#pragma once
#ifndef BFME2_GADGETTEXTENTRY_H
#define BFME2_GADGETTEXTENTRY_H

#include "GameClient/GameWindow.h"

class AsciiString;
class UnicodeString;
class GameFont;
class Image;

// The validation flags the script parser sets for a text entry (GadgetTextEntrySetValidationFlags 0x0032060D
// writes the same word): the order of the NUMERICALONLY, ALPHANUMERICALONLY and ASCIIONLY keys in a window block.
enum
{
	GADGET_ENTRY_ASCII_ONLY = 0x10,
	GADGET_ENTRY_NUMERICAL_ONLY = 0x20,
	GADGET_ENTRY_ALPHANUMERICAL_ONLY = 0x40
};

// The text entry's user data (GameWindow::winGetUserData): the validation flags, the maximum length, the secret text
// flag and the cursor and the anchor of the selection are established; the rest is not recovered.
struct GadgetTextEntryData
{
	unsigned char m_gap0x0[0xC];
	unsigned int m_validationFlags;		// +0x0C
	short m_maxTextLen;					// +0x10
	bool m_secretText;					// +0x12
	unsigned char m_gap0x13[0x1C - 0x13];
	short m_charPos;		// +0x1C (HasSelection 0x00444016 compares it with the next word)
	short m_conCharPos;		// +0x1E
};

void GadgetTextEntrySetText(GameWindow *, UnicodeString);	// 0x002C17EB
class BfmeKeyLC;
void GadgetTextEntrySetMaxChars(BfmeKeyLC *, unsigned short);	// 0x00433D07 (the map's spelling)
void GadgetTextEntrySetValidationFlags(GameWindow *, int);	// 0x0032060D
void GadgetTextEntrySetFont(GameWindow *, GameFont *);	// 0x00320641
void GadgetTextEntrySetCursorPosition(GameWindow *, unsigned int);	// 0x00320737
WindowMsgHandledType GadgetTextEntrySystem(GameWindow *, unsigned int, unsigned int, unsigned int);	// 0x003207F5
UnicodeString GadgetTextEntryGetText(GameWindow *);	// 0x00320AAB
bool GadgetTextEntryUpdateComposition(GameWindow *);	// 0x00320B3C
bool GadgetTextEntryInsertCharacter(GameWindow *, unsigned int);	// 0x00320C6F
WindowMsgHandledType GadgetTextEntryInput(GameWindow *, unsigned int, unsigned int, unsigned int);	// 0x00320DA9
void GadgetTextEntrySetTextColor(GameWindow *, int);	// 0x00322430
bool GadgetTextEntryHasSelection(GameWindow *);	// 0x00444016

#endif
