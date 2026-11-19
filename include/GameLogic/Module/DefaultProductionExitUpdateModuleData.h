// The spawn position and rally point for the default production exit.
#pragma once
#ifndef BFME2_DEFAULT_PRODUCTION_EXIT_UPDATE_MODULE_DATA_H
#define BFME2_DEFAULT_PRODUCTION_EXIT_UPDATE_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/ModuleData.h"
#include "Common/Coord3D.h"

class INI;
class MultiIniFieldParse;

class DefaultProductionExitUpdateModuleData : public ModuleData
{
public:
	DefaultProductionExitUpdateModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);

	Coord3D m_unitCreatePoint;                             // +0x8 UnitCreatePoint
	Coord3D m_naturalRallyPoint;                           // +0x14 NaturalRallyPoint
};
// SIZE 0x20
typedef char DefaultProductionExitUpdateModuleData_size[(sizeof(DefaultProductionExitUpdateModuleData) == 0x20) ? 1 : -1];
typedef char DefaultProductionExitUpdateModuleData_off_m_unitCreatePoint[(offsetof(DefaultProductionExitUpdateModuleData, m_unitCreatePoint) == 0x8) ? 1 : -1];
typedef char DefaultProductionExitUpdateModuleData_off_m_naturalRallyPoint[(offsetof(DefaultProductionExitUpdateModuleData, m_naturalRallyPoint) == 0x14) ? 1 : -1];

#endif
