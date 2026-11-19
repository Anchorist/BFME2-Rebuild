// The turn observer registered with LivingWorldLogic's +0x1C list.
// Native base table 0x00862A20 has two ret-8 callbacks and no deleting slot.
// The region manager overrides both. LivingWorldArmy overrides only BeginTurn.
#pragma once

#include "Common/GameType.h"

class LivingWorldTurnObserver
{
public:
	virtual void BeginTurn(Int, Int) {}
	virtual void OnTurnEnding(Int, Int) {}
};
