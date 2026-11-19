#pragma once

#include "GameLogic/PartitionFilter.h"

class Player;

// Keeps objects controlled by the supplied player and provides that player's query mask.
class PartitionFilterSamePlayer : public PartitionFilter
{
public:
	PartitionFilterSamePlayer(const Player *player) : m_player(player) {}
	virtual bool allow(Object *object);
	virtual int getPlayerMask();

private:
	const Player *m_player;
};
