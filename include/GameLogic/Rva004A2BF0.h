// Rva004A2BF0.h: the stealth detector's player-facing filter. SIZE 0xC.
// Target facts: allow 0x004A2BF0 asks the object's 0x002943B2 about the player
// at +0x08 and then the object's +0x250 interface for slots 4 (+0x10) and 73
// (+0x124), the garrison and stealthed-occupant queries on ContainModuleInterface.
#pragma once
#ifndef BFME2_RVA004A2BF0_H
#define BFME2_RVA004A2BF0_H

#include "Common/GameType.h"

class Object;
class Player;

class Rva004A2BF0
{
public:
	Bool allow(Object *obj);

	UnsignedByte m_unk0x00[8];
	const Player *m_player;								// 0x08
};
// SIZE 0xC

#endif
