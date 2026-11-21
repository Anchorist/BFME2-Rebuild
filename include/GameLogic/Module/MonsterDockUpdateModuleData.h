// The MonsterDock parser extends DockUpdate data with a filter and timer.
// Retail ctor 0x4A1517 constructs the base, then the filter at +0x10.
#pragma once
#ifndef BFME2_MONSTER_DOCK_UPDATE_MODULE_DATA_H
#define BFME2_MONSTER_DOCK_UPDATE_MODULE_DATA_H

#include "GameLogic/Module/DockUpdate.h"
#include "GameLogic/ObjectFilter.h"

class MonsterDockUpdateModuleData : public DockUpdateModuleData
{
public:
	MonsterDockUpdateModuleData();
	virtual ~MonsterDockUpdateModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);

	ObjectFilter m_dockableObjectFilter;   // +0x10
	UnsignedInt m_dockedAnimationTime;      // +0x14
};
typedef char MonsterDockUpdateModuleDataSize[(sizeof(MonsterDockUpdateModuleData) == 0x18) ? 1 : -1];

#endif
