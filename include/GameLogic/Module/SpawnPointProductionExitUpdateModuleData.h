// The bone that identifies the production spawn point.
#pragma once
#ifndef BFME2_SPAWN_POINT_PRODUCTION_EXIT_UPDATE_MODULE_DATA_H
#define BFME2_SPAWN_POINT_PRODUCTION_EXIT_UPDATE_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/ModuleData.h"
#include "Common/AsciiString.h"

class INI;
class MultiIniFieldParse;

class SpawnPointProductionExitUpdateModuleData : public ModuleData
{
public:
	SpawnPointProductionExitUpdateModuleData() {}
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);

	AsciiString m_spawnPointBoneName;                      // +0x8 SpawnPointBoneName
};
// SIZE 0xC
typedef char SpawnPointProductionExitUpdateModuleData_size[(sizeof(SpawnPointProductionExitUpdateModuleData) == 0xC) ? 1 : -1];
typedef char SpawnPointProductionExitUpdateModuleData_off_m_spawnPointBoneName[(offsetof(SpawnPointProductionExitUpdateModuleData, m_spawnPointBoneName) == 0x8) ? 1 : -1];

#endif
