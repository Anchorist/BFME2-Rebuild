// AiOrdersManager.h: the manager of the AI's group orders (TheAiOrdersManager).
// Target facts: TheAiOrdersManager is a pointer at VA 0x00E01E18
// (?TheAiOrdersManager@@3PAVAiOrdersManager@@A in symbols.json). Player's
// per-object callbacks 0x002AA264 and 0x002AA27A (the iterate wrappers 0x002ABAA6
// and 0x002ABAB3) load it and call rva0035519E(object ID) and clearOrders(2,
// object ID). Both methods look the ID up through 0x0035516C and forward to the
// found entry. The class layout is not recovered yet; only the methods callers use
// are declared, as the map spells them.
#pragma once
#ifndef BFME2_AIORDERSMANAGER_H
#define BFME2_AIORDERSMANAGER_H

#include "Common/GameType.h"

class AiOrdersManager
{
public:
	void clearOrders(Int unk, Int objectID);
	void rva0035519E(Int objectID);
	void rva003551EA(Int objectID) const;			// (Player::rva002AABBC 0x002AABBC calls it for every object of the current selection)
};

extern AiOrdersManager *TheAiOrdersManager;		// VA 0x00E01E18

#endif
