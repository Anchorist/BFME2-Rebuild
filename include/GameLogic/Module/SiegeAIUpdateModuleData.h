#pragma once
#ifndef BFME2_SIEGE_A_I_UPDATE_MODULE_DATA_H
#define BFME2_SIEGE_A_I_UPDATE_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/AIUpdate.h"

class MultiIniFieldParse;

// Siege uses the base AI data layout without additional storage.
class SiegeAIUpdateModuleData : public AIUpdateModuleData
{
public:
	SiegeAIUpdateModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
};
typedef char SiegeAIUpdateModuleData_size[(sizeof(SiegeAIUpdateModuleData) == 0x64) ? 1 : -1];

#endif
