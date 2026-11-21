// RankPointValue.h: rank threshold table and rank display helpers (GameNetwork/RankPointValue.cpp).
// Target facts (retail game.dat): the threshold-table class holds eleven Int thresholds at +0x00..+0x28;
// the class name Rva00559AC1 and constructor-like initializer rva00559A76(Int) are forced by the
// ledger's placeholder keys until renamed.
#pragma once
#ifndef BFME2_RANKPOINTVALUE_H
#define BFME2_RANKPOINTVALUE_H

#include "Common/GameType.h"
#include "Common/UnicodeString.h"

class Image;

class Rva00559AC1
{
public:
	Rva00559AC1 *rva00559A76(Int dummy);
	Int rva00559AC1(Int points);
	Int rva00559ADC(Int points);
	Real PercentDoneUntilNextRank(Int points);
	const Image *rva00559C25(Int side, Int points);

private:
	Int m_vals[11];									// +0x00..+0x28: eleven rank thresholds
};

UnsignedByte __cdecl Rva00559B4BCheck(Int side);
const Image *__cdecl GetRankIcon(Int side, Int rank);
UnicodeString __cdecl Rva00559C3D(UnsignedByte isEvil, Int rank);
UnicodeString __cdecl Rva00559CE5(Int side, Int rank);

#endif
