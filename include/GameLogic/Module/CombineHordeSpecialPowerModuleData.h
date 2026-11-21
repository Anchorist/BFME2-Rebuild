// Retail constructor 0x4C886E installs table VA 0x85E7A8 over SpecialPowerModuleData.
// The matching INI entry is reached through buildFieldParse at 0x4C87A9.
#pragma once

#include <stddef.h>
#include "GameLogic/Module/SpecialPowerModuleData.h"

class MultiIniFieldParse;

class CombineHordeSpecialPowerModuleData : public SpecialPowerModuleData
{
public:
	CombineHordeSpecialPowerModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);

	Real m_scanRange;
};

typedef char CombineHordeSpecialPowerModuleDataSizeCheck[sizeof(CombineHordeSpecialPowerModuleData) == 0x80 ? 1 : -1];
typedef char CombineHordeSpecialPowerModuleDataFieldCheck[offsetof(CombineHordeSpecialPowerModuleData, m_scanRange) == 0x7C ? 1 : -1];
