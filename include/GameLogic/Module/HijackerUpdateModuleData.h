// The attachment bone and parachute settings used after a hijack.
#pragma once
#ifndef BFME2_HIJACKER_UPDATE_MODULE_DATA_H
#define BFME2_HIJACKER_UPDATE_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/ModuleData.h"
#include "Common/AsciiString.h"

class INI;
class MultiIniFieldParse;

class HijackerUpdateModuleData : public ModuleData
{
public:
	HijackerUpdateModuleData() {}
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);

	AsciiString m_attachToTargetBone;                      // +0x8 AttachToTargetBone
	AsciiString m_parachuteName;                           // +0xC ParachuteName
};
// SIZE 0x10
typedef char HijackerUpdateModuleData_size[(sizeof(HijackerUpdateModuleData) == 0x10) ? 1 : -1];
typedef char HijackerUpdateModuleData_off_m_attachToTargetBone[(offsetof(HijackerUpdateModuleData, m_attachToTargetBone) == 0x8) ? 1 : -1];
typedef char HijackerUpdateModuleData_off_m_parachuteName[(offsetof(HijackerUpdateModuleData, m_parachuteName) == 0xC) ? 1 : -1];

#endif
