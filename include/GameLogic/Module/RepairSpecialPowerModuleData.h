// Native factory uses the 0x7C-byte SpecialPowerModuleData layout. The
// shared 0x4C72D3 constructor supplies the same table and performs no leaf stores.
#pragma once

#include "GameLogic/Module/SpecialPowerModuleData.h"

class RepairSpecialPowerModuleData : public SpecialPowerModuleData
{
public:
	RepairSpecialPowerModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);
};

typedef char RepairSpecialPowerModuleDataSizeCheck[sizeof(RepairSpecialPowerModuleData) == 0x7C ? 1 : -1];
