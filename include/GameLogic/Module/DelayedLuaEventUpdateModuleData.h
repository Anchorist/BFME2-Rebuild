#pragma once
#ifndef BFME2_DELAYED_LUA_EVENT_UPDATE_MODULE_DATA_H
#define BFME2_DELAYED_LUA_EVENT_UPDATE_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/ModuleData.h"

class MultiIniFieldParse;

class DelayedLuaEventUpdateModuleData : public ModuleData
{
public:
	DelayedLuaEventUpdateModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);
};
typedef char DelayedLuaEventUpdateModuleData_size[(sizeof(DelayedLuaEventUpdateModuleData) == 0x8) ? 1 : -1];

#endif
