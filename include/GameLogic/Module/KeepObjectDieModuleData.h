// How long a dying object stays present and whether it stays on the radar.
#pragma once
#ifndef BFME2_KEEP_OBJECT_DIE_MODULE_DATA_H
#define BFME2_KEEP_OBJECT_DIE_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/DestroyDieModuleData.h"

class INI;
class MultiIniFieldParse;

// Base DestroyDieModuleData: the constructor calls its constructor on this. It ends at 0x38 (its own operator-new size);
// this class's members follow it.
typedef char KeepObjectDieModuleData_base_size[(sizeof(DestroyDieModuleData) == 0x38) ? 1 : -1];

class KeepObjectDieModuleData : public DestroyDieModuleData
{
public:
	KeepObjectDieModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);

	UnsignedInt m_collapsingTime;                          // +0x38 CollapsingTime; duration, frames
	Bool m_stayOnRadar;                                    // +0x3C StayOnRadar
};
// SIZE 0x40
typedef char KeepObjectDieModuleData_size[(sizeof(KeepObjectDieModuleData) == 0x40) ? 1 : -1];
typedef char KeepObjectDieModuleData_off_m_collapsingTime[(offsetof(KeepObjectDieModuleData, m_collapsingTime) == 0x38) ? 1 : -1];
typedef char KeepObjectDieModuleData_off_m_stayOnRadar[(offsetof(KeepObjectDieModuleData, m_stayOnRadar) == 0x3C) ? 1 : -1];

#endif
