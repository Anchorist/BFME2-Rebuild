// The invisibility update settings and its required and forbidden upgrades.
#pragma once
#ifndef BFME2_INVISIBILITY_UPDATE_MODULE_DATA_H
#define BFME2_INVISIBILITY_UPDATE_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/ModuleData.h"
#include "GameLogic/ObjectFilter.h"
#include "Common/AsciiString.h"
#include "Common/UpgradeMaskType.h"

class INI;
class MultiIniFieldParse;

class InvisibilityUpdateModuleData : public ModuleData
{
public:
	static ModuleData *friend_newModuleData(INI *ini);
	InvisibilityUpdateModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);

	UnsignedByte m_invisibilityNugget[0xB8];               // +0x8 InvisibilityNugget; unresolved: Rva00438176Parse
	UnsignedInt m_updatePeriod;                            // +0xC0 UpdatePeriod; duration, frames
	UpgradeMaskType m_requiredUpgrades;	// RequiredUpgrades
	UpgradeMaskType m_forbiddenUpgrades;	// ForbiddenUpgrades
	Bool m_broadcast;                                      // +0x1C4 Broadcast
	ObjectFilter m_broadcastObjectFilter;                  // +0x1C8 BroadcastObjectFilter
	Real m_broadcastRange;                                 // +0x1CC BroadcastRange
	Bool m_startsActive;                                   // +0x1D0 StartsActive
	AsciiString m_unitSpecificSoundNameToUseAsVoiceMoveToStealthyArea;// +0x1D4 UnitSpecificSoundNameToUseAsVoiceMoveToStealthyArea
	AsciiString m_unitSpecificSoundNameToUseAsVoiceEnterStateMoveToStealthyArea;// +0x1D8 UnitSpecificSoundNameToUseAsVoiceEnterStateMoveToStealthyArea
};
// SIZE 0x1DC
typedef char InvisibilityUpdateModuleData_size[(sizeof(InvisibilityUpdateModuleData) == 0x1DC) ? 1 : -1];
typedef char InvisibilityUpdateModuleData_off_m_invisibilityNugget[(offsetof(InvisibilityUpdateModuleData, m_invisibilityNugget) == 0x8) ? 1 : -1];
typedef char InvisibilityUpdateModuleData_off_m_updatePeriod[(offsetof(InvisibilityUpdateModuleData, m_updatePeriod) == 0xC0) ? 1 : -1];
typedef char InvisibilityUpdateModuleData_off_m_requiredUpgrades[(offsetof(InvisibilityUpdateModuleData, m_requiredUpgrades) == 0xC4) ? 1 : -1];
typedef char InvisibilityUpdateModuleData_off_m_forbiddenUpgrades[(offsetof(InvisibilityUpdateModuleData, m_forbiddenUpgrades) == 0x144) ? 1 : -1];
typedef char InvisibilityUpdateModuleData_off_m_broadcast[(offsetof(InvisibilityUpdateModuleData, m_broadcast) == 0x1C4) ? 1 : -1];
typedef char InvisibilityUpdateModuleData_off_m_broadcastObjectFilter[(offsetof(InvisibilityUpdateModuleData, m_broadcastObjectFilter) == 0x1C8) ? 1 : -1];
typedef char InvisibilityUpdateModuleData_off_m_broadcastRange[(offsetof(InvisibilityUpdateModuleData, m_broadcastRange) == 0x1CC) ? 1 : -1];
typedef char InvisibilityUpdateModuleData_off_m_startsActive[(offsetof(InvisibilityUpdateModuleData, m_startsActive) == 0x1D0) ? 1 : -1];
typedef char InvisibilityUpdateModuleData_off_m_unitSpecificSoundNameToUseAsVoiceMoveToStealthyArea[(offsetof(InvisibilityUpdateModuleData, m_unitSpecificSoundNameToUseAsVoiceMoveToStealthyArea) == 0x1D4) ? 1 : -1];
typedef char InvisibilityUpdateModuleData_off_m_unitSpecificSoundNameToUseAsVoiceEnterStateMoveToStealthyArea[(offsetof(InvisibilityUpdateModuleData, m_unitSpecificSoundNameToUseAsVoiceEnterStateMoveToStealthyArea) == 0x1D8) ? 1 : -1];

#endif
