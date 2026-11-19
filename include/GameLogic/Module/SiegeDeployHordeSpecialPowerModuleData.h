// Retail constructor 0x4C64D3 installs table VA 0x85DAB0 over SpecialPowerUpdateModuleData.
// The matching INI entry is reached through buildFieldParse at 0x4C636B.
#pragma once

#include <stddef.h>
#include "GameLogic/Module/SpecialPowerUpdateModule.h"

class MultiIniFieldParse;

class SiegeDeployHordeSpecialPowerModuleData : public SpecialPowerUpdateModuleData
{
public:
	SiegeDeployHordeSpecialPowerModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);

	Bool m_hordeDeploy;
};

typedef char SiegeDeployHordeSpecialPowerModuleDataSizeCheck[sizeof(SiegeDeployHordeSpecialPowerModuleData) == 0x1C ? 1 : -1];
typedef char SiegeDeployHordeSpecialPowerModuleDataFieldCheck[offsetof(SiegeDeployHordeSpecialPowerModuleData, m_hordeDeploy) == 0x18 ? 1 : -1];
