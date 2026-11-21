#pragma once
#ifndef BFME2_HORDE_TRANSPORT_CONTAIN_DAMAGE_MODULE_DATA_H
#define BFME2_HORDE_TRANSPORT_CONTAIN_DAMAGE_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/ModuleData.h"

class MultiIniFieldParse;

class HordeTransportContainDamageModuleData : public ModuleData
{
public:
	HordeTransportContainDamageModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);
};
typedef char HordeTransportContainDamageModuleData_size[(sizeof(HordeTransportContainDamageModuleData) == 0x8) ? 1 : -1];

#endif
