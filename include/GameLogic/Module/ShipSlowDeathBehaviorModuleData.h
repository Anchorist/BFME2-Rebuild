#pragma once
#ifndef BFME2_SHIP_SLOW_DEATH_BEHAVIOR_MODULE_DATA_H
#define BFME2_SHIP_SLOW_DEATH_BEHAVIOR_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/SlowDeathBehaviorModuleData.h"

class MultiIniFieldParse;

// The ship module uses the shared slow-death data layout.
class ShipSlowDeathBehaviorModuleData : public SlowDeathBehaviorModuleData
{
public:
	ShipSlowDeathBehaviorModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
};
typedef char ShipSlowDeathBehaviorModuleData_size[(sizeof(ShipSlowDeathBehaviorModuleData) == 0x190) ? 1 : -1];

#endif
