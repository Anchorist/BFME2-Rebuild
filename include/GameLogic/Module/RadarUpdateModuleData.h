// The radar extension configured for this object.
#pragma once
#ifndef BFME2_RADAR_UPDATE_MODULE_DATA_H
#define BFME2_RADAR_UPDATE_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/ModuleData.h"

class INI;
class MultiIniFieldParse;

class RadarUpdateModuleData : public ModuleData
{
public:
	RadarUpdateModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);

	Real m_radarExtendTime;                                // +0x8 RadarExtendTime; duration
};
// SIZE 0xC
typedef char RadarUpdateModuleData_size[(sizeof(RadarUpdateModuleData) == 0xC) ? 1 : -1];
typedef char RadarUpdateModuleData_off_m_radarExtendTime[(offsetof(RadarUpdateModuleData, m_radarExtendTime) == 0x8) ? 1 : -1];

#endif
