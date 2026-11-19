// The SpawnerTrigger configuration applied to units created by a spawner.
#pragma once
#ifndef BFME2_SPAWNED_MODEL_CONDITION_CREATE_MODULE_DATA_H
#define BFME2_SPAWNED_MODEL_CONDITION_CREATE_MODULE_DATA_H

#include <stddef.h>
#include <vector>
#include "Common/GameType.h"
#include "Common/AsciiString.h"
#include "Common/ModelConditionFlags.h"
#include "GameLogic/Module/ModuleData.h"

class FXList;
class INI;
class MultiIniFieldParse;

// SpawnerTrigger parses a unit name, an optional effect, and two sets of
// model conditions. The source condition belongs to the spawner, the new
// condition applies to the created unit.
struct SpawnerTrigger
{
	SpawnerTrigger() : m_fx(0) {}

	AsciiString m_unitName;
	const FXList *m_fx;
	ModelConditionFlags m_newConditions;
	ModelConditionFlags m_spawnerConditions;
};
typedef char SpawnerTrigger_size[(sizeof(SpawnerTrigger) == 0xA0) ? 1 : -1];
typedef char SpawnerTrigger_off_m_spawnerConditions[(offsetof(SpawnerTrigger, m_spawnerConditions) == 0x54) ? 1 : -1];

class SpawnedModelConditionCreateModuleData : public ModuleData
{
public:
	SpawnedModelConditionCreateModuleData() throw();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);

	std::vector<SpawnerTrigger> m_spawnerTriggers;
};
// SIZE 0x14
typedef char SpawnedModelConditionCreateModuleData_size[(sizeof(SpawnedModelConditionCreateModuleData) == 0x14) ? 1 : -1];

#endif
