#pragma once
#include "GameLogic/PartitionFilter.h"
// Both WanderAIUpdate and CommandButtonHuntUpdate install table 0x007FAD10.
// Its allow() slot at 0x0026119D tests the candidate Object::isEffectivelyDead bit.
class PartitionFilterAlive : public PartitionFilter
{
public:
	virtual bool allow(Object *object);
};
