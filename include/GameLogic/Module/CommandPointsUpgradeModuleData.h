// The command-point capacity and object filters for an upgrade.
#pragma once
#ifndef BFME2_COMMAND_POINTS_UPGRADE_MODULE_DATA_H
#define BFME2_COMMAND_POINTS_UPGRADE_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/UpgradeModule.h"
#include "GameLogic/ObjectFilter.h"

class INI;
class MultiIniFieldParse;

class CommandPointsUpgradeModuleData : public UpgradeModuleData
{
public:
	CommandPointsUpgradeModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);

	Int m_commandPoints;                                   // +0x118 CommandPoints
	ObjectFilter m_requiredObject;                         // +0x11C RequiredObject
};
// SIZE 0x120
typedef char CommandPointsUpgradeModuleData_size[(sizeof(CommandPointsUpgradeModuleData) == 0x120) ? 1 : -1];
typedef char CommandPointsUpgradeModuleData_off_m_commandPoints[(offsetof(CommandPointsUpgradeModuleData, m_commandPoints) == 0x118) ? 1 : -1];
typedef char CommandPointsUpgradeModuleData_off_m_requiredObject[(offsetof(CommandPointsUpgradeModuleData, m_requiredObject) == 0x11C) ? 1 : -1];

#endif
