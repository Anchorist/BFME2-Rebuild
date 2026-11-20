// GadgetTabControl.h: the tab control gadget's free-function interface, declared from the
// names retail's own map carries (decorated names demangled; every one is a plain
// cdecl function that takes the window first). The per-gadget data struct lives in
// the window's instance data, so none of it is exposed here. Each
// declaration's comment is its retail RVA. Evidence: map identities only; the data
// layouts behind them are recovered with the functions that use them.
#pragma once
#ifndef BFME2_GADGETTABCONTROL_H
#define BFME2_GADGETTABCONTROL_H

#include "GameClient/GameWindow.h"

class AsciiString;
class UnicodeString;
class GameFont;
class Image;

// The tab control's own data (what the window's user data points at). The sub-pane table is recovered:
// GadgetTabControlResizeSubPanes 0x00327287 walks eight pane pointers starting at +0x14, and
// GadgetTabControlFixupSubPaneList 0x003272E2 fills that table from the window's children. The script parser
// (0x00315367) writes the five tab settings, the eight disabled flags and the pane border in the order of the
// window block's keys. The rest of the struct and its SIZE are not recovered here.
struct TabControlData
{
	int m_tabOrientation;				// +0x00 TABORIENTATION
	int m_tabEdge;						// +0x04 TABEDGE
	int m_tabWidth;						// +0x08 TABWIDTH
	int m_tabHeight;					// +0x0C TABHEIGHT
	int m_tabCount;						// +0x10 TABCOUNT
	GameWindow *m_subPanes[8];			// +0x14
	bool m_subPaneDisabled[8];			// +0x34 PANEDISABLED
	int m_paneBorder;					// +0x3C PANEBORDER
};

void GadgetTabControlComputeTabRegion(GameWindow *);	// 0x00327099
void GadgetTabControlComputeSubPaneSize(GameWindow *, int *, int *, int *, int *);	// 0x003271D9
void GadgetTabControlResizeSubPanes(GameWindow *);	// 0x00327287
void GadgetTabControlFixupSubPaneList(GameWindow *);	// 0x003272E2
WindowMsgHandledType GadgetTabControlSystem(GameWindow *, unsigned int, unsigned int, unsigned int);	// 0x00327330
void GadgetTabControlShowSubPane(GameWindow *, int);	// 0x0032739B
WindowMsgHandledType GadgetTabControlInput(GameWindow *, unsigned int, unsigned int, unsigned int);	// 0x003273FB
void GadgetTabControlCreateSubPanes(GameWindow *);	// 0x00327490

#endif
