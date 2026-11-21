// RankPointValue.h: rank threshold table and rank display helpers (GameNetwork/RankPointValue.cpp).
// Target facts: the map names the threshold-table class Rva00559AC1 (constructor/init 0x00559A76,
// rank lookup 0x00559AC1, distance to next rank 0x00559ADC, progress 0x00559AF9, rank icon
// wrapper 0x00559C25); it holds eleven rank thresholds at +0x00..+0x28.
#pragma once
#ifndef BFME2_RANKPOINTVALUE_H
#define BFME2_RANKPOINTVALUE_H

#include "Common/UnicodeString.h"

class Image;

class Rva00559AC1
{
public:
	Rva00559AC1 *rva00559A76(int dummy);			// 0x00559A76
	int rva00559AC1(int points);					// 0x00559AC1
	int rva00559ADC(int points);					// 0x00559ADC
	float PercentDoneUntilNextRank(int points);		// 0x00559AF9
	const Image *rva00559C25(int side, int points);	// 0x00559C25

private:
	int m_vals[11];									// +0x00..+0x28: eleven rank thresholds
};

unsigned char __cdecl Rva00559B4BCheck(int side);				// 0x00559B4B
const Image *__cdecl GetRankIcon(int side, int rank);			// 0x00559B64
UnicodeString __cdecl Rva00559C3D(unsigned char isEvil, int rank);	// 0x00559C3D
UnicodeString __cdecl Rva00559CE5(int side, int rank);			// 0x00559CE5

#endif
