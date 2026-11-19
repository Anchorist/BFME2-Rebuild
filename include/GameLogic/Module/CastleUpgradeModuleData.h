// CastleUpgrade data extends UpgradeModuleData with the wall upgrade fields.
// Retail ctor 0x255836 calls the UpgradeModuleData constructor 0x253487.
// Parser 0x4B6847 reads offsets +0x118 and +0x11C from table 0x8588C4.
#pragma once
#ifndef BFME2_CASTLE_UPGRADE_MODULE_DATA_H
#define BFME2_CASTLE_UPGRADE_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/UpgradeModule.h"
#include "Common/AsciiString.h"

class INI;

class CastleUpgradeModuleData : public UpgradeModuleData
{
public:
	CastleUpgradeModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);

	AsciiString m_upgrade;                                 // +0x118 Upgrade
	Real m_wallUpgradeRadius;                              // +0x11C WallUpgradeRadius
};
typedef char CastleUpgradeModuleData_size[(sizeof(CastleUpgradeModuleData) == 0x120) ? 1 : -1];
typedef char CastleUpgradeModuleData_off_m_upgrade[(offsetof(CastleUpgradeModuleData, m_upgrade) == 0x118) ? 1 : -1];
typedef char CastleUpgradeModuleData_off_m_wallUpgradeRadius[(offsetof(CastleUpgradeModuleData, m_wallUpgradeRadius) == 0x11C) ? 1 : -1];

#endif
