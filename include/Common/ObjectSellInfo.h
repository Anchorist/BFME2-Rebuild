#pragma once

#include "Common/GameType.h"

class ObjectSellInfo
{
public:
	ObjectSellInfo();
	virtual ~ObjectSellInfo();

	// BuildAssistant::sellObject records the selected object's ID and the current game frame.
	ObjectID m_id;
	UnsignedInt m_sellFrame;
};
