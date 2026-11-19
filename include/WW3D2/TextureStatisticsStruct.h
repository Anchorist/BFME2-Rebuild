// Portions derived from Command & Conquer Generals and Command & Conquer Generals Zero Hour, (c) Electronic Arts Inc., GPL-3.0-or-later; see LICENSE and NOTICE.
#pragma once
#ifndef BFME2_TEXTURESTATISTICSSTRUCT_H
#define BFME2_TEXTURESTATISTICSSTRUCT_H

#include "WW3D2/TextureAsset.h"

struct TextureStatisticsStruct
{
	TextureAsset Texture;
	int UsageCount;
	int ChangeCount;

	bool operator==(const TextureStatisticsStruct &that) const
	{
		return Texture == that.Texture;
	}
};

typedef char TextureStatisticsStructSize[(sizeof(TextureStatisticsStruct) == 0xC) ? 1 : -1];

#endif
