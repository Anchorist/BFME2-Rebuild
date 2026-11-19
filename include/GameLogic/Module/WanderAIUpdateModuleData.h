// The pathing and entry settings for a wandering AI unit.
#pragma once
#ifndef BFME2_WANDER_A_I_UPDATE_MODULE_DATA_H
#define BFME2_WANDER_A_I_UPDATE_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/AIUpdate.h"

class INI;
class MultiIniFieldParse;

// Base AIUpdateModuleData: the constructor calls its constructor on this. It ends at 0x64 (its own operator-new size);
// this class's members follow it.
typedef char WanderAIUpdateModuleData_base_size[(sizeof(AIUpdateModuleData) == 0x64) ? 1 : -1];

class WanderAIUpdateModuleData : public AIUpdateModuleData
{
public:
	WanderAIUpdateModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);

	Bool m_wildBeast;                                      // +0x64 WildBeast
	UnsignedByte m_unk0x65[0x3];
	Int m_conditionForEntry;	// Entry condition index, or -1 when unset.
	Bool m_selectable;                                     // +0x6C Selectable
	UnsignedInt m_wanderDistance;                          // +0x70 WanderDistance
};
// SIZE 0x74
typedef char WanderAIUpdateModuleData_size[(sizeof(WanderAIUpdateModuleData) == 0x74) ? 1 : -1];
typedef char WanderAIUpdateModuleData_off_m_wildBeast[(offsetof(WanderAIUpdateModuleData, m_wildBeast) == 0x64) ? 1 : -1];
typedef char WanderAIUpdateModuleData_off_m_conditionForEntry[(offsetof(WanderAIUpdateModuleData, m_conditionForEntry) == 0x68) ? 1 : -1];
typedef char WanderAIUpdateModuleData_off_m_selectable[(offsetof(WanderAIUpdateModuleData, m_selectable) == 0x6C) ? 1 : -1];
typedef char WanderAIUpdateModuleData_off_m_wanderDistance[(offsetof(WanderAIUpdateModuleData, m_wanderDistance) == 0x70) ? 1 : -1];

#endif
