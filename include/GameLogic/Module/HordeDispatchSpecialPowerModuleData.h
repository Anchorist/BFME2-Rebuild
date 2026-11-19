// Retail constructor 0x4C72D3 installs table VA 0x85E7A8 over SpecialPowerModuleData.
// The matching INI entry is reached through buildFieldParse at 0x4C89CB.
#pragma once

#include <stddef.h>
#include "GameLogic/Module/SpecialPowerModuleData.h"

class MultiIniFieldParse;

class HordeDispatchSpecialPowerModuleData : public SpecialPowerModuleData
{
public:
	HordeDispatchSpecialPowerModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
};

typedef char HordeDispatchSpecialPowerModuleDataSizeCheck[sizeof(HordeDispatchSpecialPowerModuleData) == 0x7C ? 1 : -1];
