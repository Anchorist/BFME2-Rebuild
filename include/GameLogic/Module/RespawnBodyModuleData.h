// Respawn configuration extends ActiveBodyModuleData with its own INI fields.
#pragma once
#ifndef BFME2_RESPAWN_BODY_MODULE_DATA_H
#define BFME2_RESPAWN_BODY_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/ActiveBodyModuleData.h"
#include "GameLogic/ObjectFilter.h"

class INI;
class MultiIniFieldParse;

// Base ActiveBodyModuleData: the constructor calls its constructor on this. It ends at 0x64 (its own operator-new size);
// this class's members follow it.
typedef char RespawnBodyModuleData_base_size[(sizeof(ActiveBodyModuleData) == 0x64) ? 1 : -1];

class RespawnBodyModuleData : public ActiveBodyModuleData
{
public:
	RespawnBodyModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);

	ObjectFilter m_permanentlyKilledByFilter;              // +0x64 PermanentlyKilledByFilter
	Bool m_canRespawn;                                     // +0x68 CanRespawn
};
// SIZE 0x6C
typedef char RespawnBodyModuleData_size[(sizeof(RespawnBodyModuleData) == 0x6C) ? 1 : -1];
typedef char RespawnBodyModuleData_off_m_permanentlyKilledByFilter[(offsetof(RespawnBodyModuleData, m_permanentlyKilledByFilter) == 0x64) ? 1 : -1];
typedef char RespawnBodyModuleData_off_m_canRespawn[(offsetof(RespawnBodyModuleData, m_canRespawn) == 0x68) ? 1 : -1];

#endif
