// Native deploy configuration. The 0x30-byte factory at 0x2521A3 calls
// 0x4C5815, which initializes SpecialPowerUpdateModuleData before these fields.
#pragma once

#include <stddef.h>
#include "GameLogic/Module/SpecialPowerUpdateModule.h"

class SiegeDeploySpecialPowerModuleData : public SpecialPowerUpdateModuleData
{
public:
	SiegeDeploySpecialPowerModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);

	UnsignedInt m_lowerDelay;
	UnsignedInt m_raiseDelay;
	Bool m_evacuatePassengersOnDeploy;
	Bool m_evacuateCrewOnDeploy;
	Bool m_skipAdjustPosition;
	Real m_wallSearchDistance;
	Real m_awayFromWallWaitDist;
	Real m_extraWallDistance;
};

typedef char SiegeDeployDataSizeCheck[sizeof(SiegeDeploySpecialPowerModuleData) == 0x30 ? 1 : -1];
typedef char SiegeDeployDelayOffset[offsetof(SiegeDeploySpecialPowerModuleData, m_lowerDelay) == 0x18 ? 1 : -1];
typedef char SiegeDeployWallOffset[offsetof(SiegeDeploySpecialPowerModuleData, m_wallSearchDistance) == 0x24 ? 1 : -1];
