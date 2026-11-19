// AptCallbackHost.h: the base every Apt screen and Apt sub-panel carries. It is the class the
// map spells Rva005248D0 (its destructor 0x005248D0; constructor 0x002D2C34).
//
// Target facts (retail game.dat, RVAs; table addresses are VAs):
//  - SIZE 0x58. One virtual, the destructor: its table VA 0x00C02A80 has one slot (the map's
//    vtable record says "slots 1"); a derived class installs its own table over it.
// Constructor 0x2D2C34 builds the six registry members below. Destructor 0x5248D0
// restores its table and releases each registry in reverse. The over-button
// registry's native 0x523F8C cleanup walks both four-byte names and eight-byte
// (movie level, name) entries. The other five cleanup loops all use four-byte names.
// A screen's secondary vtable is this class's (one slot, a deleting-destructor adjustor thunk).
#pragma once
#ifndef BFME2_APTCALLBACKHOST_H
#define BFME2_APTCALLBACKHOST_H

#include <stddef.h>
#include "GameClient/AptCallbackAdders.h"

class AptCallbackHost
{
public:
	AptCallbackHost();					// 0x002D2C34 (the map names the class Rva005248D0)
	virtual ~AptCallbackHost();			// 0x005248D0 body, slot 0

	AptCommandMapAdder m_commands;  // +0x04, destroyed via 0x52413E
	AptExternHandlerAdder m_externalHandlers;  // +0x10, 0x5241B0
	AptOverButtonHandlerAdder m_overButtonHandlers;  // +0x1C, 0x524436
	AptCustomRenderAdder m_customRenderers;  // +0x34, 0x524265
	AptCallbackAdders m_assets;  // +0x40, 0x5242D7
	_STL::vector<AsciiString> m_unk0x4C;  // native name cleanup 0x524056
};
typedef char AptCallbackHostOverButtonsOffset[offsetof(AptCallbackHost, m_overButtonHandlers) == 0x1C ? 1 : -1];
typedef char AptCallbackHostAssetsOffset[offsetof(AptCallbackHost, m_assets) == 0x40 ? 1 : -1];
typedef char AptCallbackHostSizeCheck[sizeof(AptCallbackHost)==0x58 ? 1 : -1];

#endif
