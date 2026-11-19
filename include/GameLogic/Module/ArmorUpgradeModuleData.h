// Configures whether an upgrade applies or removes an armor set.
#pragma once

#include <stddef.h>
#include "Common/ArmorSetType.h"
#include "GameLogic/Module/UpgradeModule.h"

class ArmorUpgradeModuleData : public UpgradeModuleData
{
public:
	Bool m_killArmorUpgrade;
	Bool m_ignoreArmorUpgrade;
	ArmorSetType m_armorSetType;
};

typedef char ArmorUpgradeModuleData_size[(sizeof(ArmorUpgradeModuleData) == 0x120) ? 1 : -1];
typedef char ArmorUpgradeModuleData_off_m_killArmorUpgrade[(offsetof(ArmorUpgradeModuleData, m_killArmorUpgrade) == 0x118) ? 1 : -1];
typedef char ArmorUpgradeModuleData_off_m_ignoreArmorUpgrade[(offsetof(ArmorUpgradeModuleData, m_ignoreArmorUpgrade) == 0x119) ? 1 : -1];
typedef char ArmorUpgradeModuleData_off_m_armorSetType[(offsetof(ArmorUpgradeModuleData, m_armorSetType) == 0x11C) ? 1 : -1];
