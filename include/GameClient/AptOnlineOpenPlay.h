// OnlineOpenPlay shares the custom-match screen layout. Retail constructor
// 0x5BA1FD replaces the three inherited tables at offsets 0, 0x60 and 0x6C.
#pragma once

#include "GameClient/AptOnlineCustomMatch.h"

class AptOnline;

class AptOnlineOpenPlay : public AptOnlineCustomMatch
{
public:
	explicit AptOnlineOpenPlay(AptOnline *screen);
	virtual ~AptOnlineOpenPlay();

	virtual const char *slot10();
};

typedef char AptOnlineOpenPlaySizeCheck[sizeof(AptOnlineOpenPlay) == 0x4E0 ? 1 : -1];
