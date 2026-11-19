// Configures whether to remove the locomotor set assigned by an upgrade.
#pragma once

#include <stddef.h>
#include "GameLogic/Module/UpgradeModule.h"

class LocomotorSetUpgradeModuleData : public UpgradeModuleData
{
public:
	Bool m_killLocomotorUpgrade;
};

typedef char LocomotorSetUpgradeModuleData_size[(sizeof(LocomotorSetUpgradeModuleData) == 0x11C) ? 1 : -1];
typedef char LocomotorSetUpgradeModuleData_off_m_killLocomotorUpgrade[(offsetof(LocomotorSetUpgradeModuleData, m_killLocomotorUpgrade) == 0x118) ? 1 : -1];
