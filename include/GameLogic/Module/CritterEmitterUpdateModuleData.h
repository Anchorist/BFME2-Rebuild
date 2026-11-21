// The effects and objects emitted when a critter spawn reloads.
#pragma once
#ifndef BFME2_CRITTER_EMITTER_UPDATE_MODULE_DATA_H
#define BFME2_CRITTER_EMITTER_UPDATE_MODULE_DATA_H

#include <stddef.h>
#include <vector>
#include "Common/GameType.h"
#include "GameLogic/Module/ModuleData.h"

class INI;
class FXList;
class ObjectCreationList;
class MultiIniFieldParse;

class CritterEmitterUpdateModuleData : public ModuleData
{
public:
	CritterEmitterUpdateModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);

	// s02: two pointer vectors. onCollide 0x004C8E83 plays a random entry of +0x8 through
	// FXList::doFXObj and creates a random entry of +0x14 through ObjectCreationList::create;
	// the ctor 0x004C8EFF builds both, the implicit dtor 0x004C8F49 frees both.
	std::vector<const FXList *> m_fx;                       // +0x8 FX (iniParseFXListVec)
	std::vector<const ObjectCreationList *> m_ocl;          // +0x14
	UnsignedInt m_reloadTime;                              // +0x20 ReloadTime; duration, frames
};
// SIZE 0x24
typedef char CritterEmitterUpdateModuleData_size[(sizeof(CritterEmitterUpdateModuleData) == 0x24) ? 1 : -1];
typedef char CritterEmitterUpdateModuleData_off_m_fx[(offsetof(CritterEmitterUpdateModuleData, m_fx) == 0x8) ? 1 : -1];
typedef char CritterEmitterUpdateModuleData_off_m_reloadTime[(offsetof(CritterEmitterUpdateModuleData, m_reloadTime) == 0x20) ? 1 : -1];

#endif
