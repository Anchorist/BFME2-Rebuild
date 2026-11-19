// The command buttons to invoke when an upgrade is added or removed.
#pragma once
#ifndef BFME2_DO_COMMAND_UPGRADE_MODULE_DATA_H
#define BFME2_DO_COMMAND_UPGRADE_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/UpgradeModule.h"
#include "Common/AsciiString.h"

class INI;
class MultiIniFieldParse;

class DoCommandUpgradeModuleData : public UpgradeModuleData
{
public:
	DoCommandUpgradeModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);

	AsciiString m_getUpgradeCommandButtonName;             // +0x118 GetUpgradeCommandButtonName
	AsciiString m_removeUpgradeCommandButtonName;          // +0x11C RemoveUpgradeCommandButtonName
};
// SIZE 0x120
typedef char DoCommandUpgradeModuleData_size[(sizeof(DoCommandUpgradeModuleData) == 0x120) ? 1 : -1];
typedef char DoCommandUpgradeModuleData_off_m_getUpgradeCommandButtonName[(offsetof(DoCommandUpgradeModuleData, m_getUpgradeCommandButtonName) == 0x118) ? 1 : -1];
typedef char DoCommandUpgradeModuleData_off_m_removeUpgradeCommandButtonName[(offsetof(DoCommandUpgradeModuleData, m_removeUpgradeCommandButtonName) == 0x11C) ? 1 : -1];

#endif
