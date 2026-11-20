// The module that chooses when the AI uses a configured special power.
#pragma once
#ifndef BFME2_A_I_SPECIAL_POWER_UPDATE_H
#define BFME2_A_I_SPECIAL_POWER_UPDATE_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/UpdateModule.h"

class Thing;
class ModuleData;
class Xfer;

// UpdateModule ends at 0x20; this class's members follow it.
typedef char AISpecialPowerUpdate_base_size[(sizeof(UpdateModule) == 0x20) ? 1 : -1];

class AISpecialPowerUpdate : public UpdateModule
{
public:
	AISpecialPowerUpdate(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	const char *name() const;   // (non-virtual literal name getter, QBE)
	virtual const char *GetSnapshotName() const;
	virtual ~AISpecialPowerUpdate();
	virtual void mapLoadPostProcess(const Dict *properties);

protected:
	virtual void xfer(Xfer *xfer);

public:
	Bool m_unk0x20;                                // +0x20; xfer Bool
	Bool m_unk0x21;                                // +0x21; xfer Bool
	Int m_unk0x24;                                 // +0x24; constructor store
protected:
	virtual void loadPostProcess() { UpdateModule::loadPostProcess(); }	// retail slot 1 0x00497805: a jmp to UpdateModule's

private:
	void postInitAISpecialPower();
};
// SIZE 0x28
typedef char AISpecialPowerUpdate_size[(sizeof(AISpecialPowerUpdate) == 0x28) ? 1 : -1];
typedef char AISpecialPowerUpdate_off_m_unk0x20[(offsetof(AISpecialPowerUpdate, m_unk0x20) == 0x20) ? 1 : -1];
typedef char AISpecialPowerUpdate_off_m_unk0x21[(offsetof(AISpecialPowerUpdate, m_unk0x21) == 0x21) ? 1 : -1];
typedef char AISpecialPowerUpdate_off_m_unk0x24[(offsetof(AISpecialPowerUpdate, m_unk0x24) == 0x24) ? 1 : -1];

#endif
