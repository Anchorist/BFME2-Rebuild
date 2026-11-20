// LargeGroupAudioUpdate: the LargeGroupAudioUpdate update module. SIZE 0x94: UpdateModule (0x20), a byte
// gap holding interface table pointers, the Coord2D at +0x28, two BitFlags that xfer (0x004AB9EA) saves at +0x30 and
// +0x7C (the 0x5C bytes between stay a gap because the flag types are not placed), the Bools at +0x8C and +0x8D and the
// Int at +0x90. The constructor (0x004AB811) runs UpdateModule's constructor and installs the tables.
#pragma once
#ifndef BFME2_LARGE_GROUP_AUDIO_UPDATE_H
#define BFME2_LARGE_GROUP_AUDIO_UPDATE_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/UpdateModule.h"
#include "Common/Coord2D.h"

class Thing;
class ModuleData;
class Xfer;

// UpdateModule ends at 0x20; this class's members follow it.
typedef char LargeGroupAudioUpdate_base_size[(sizeof(UpdateModule) == 0x20) ? 1 : -1];

class LargeGroupAudioUpdate : public UpdateModule
{
public:
	LargeGroupAudioUpdate(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual ~LargeGroupAudioUpdate();
	virtual void onObjectCreated();	// override: onObjectCreated slot 5 at +0x0 (0x004ABB37)
	void rva004AB90A();	// (onObjectCreated calls it unless +0x8D is set)
	virtual void onDelete();	// override: onDelete slot 8 at +0x0 (0x004ABB46)
	virtual UpdateSleepTime update();	// override: update slot 0 at +0x10 (0x004ABB4B)
	virtual DisabledMaskType getDisabledTypesToProcess() const;	// override: getDisabledTypesToProcess slot 1 at +0x10 (0x004AB9D5)

protected:
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

public:
	UnsignedByte m_gap0x20[0x8];
	Coord2D m_unk0x28;                             // +0x28; xfer Coord2D
	UnsignedByte m_gap0x30[0x5C];
	Bool m_unk0x8C;                                // +0x8C; xfer Bool
	Bool m_unk0x8D;                                // +0x8D; xfer Bool
	Int m_unk0x90;                                 // +0x90; xfer Int
protected:
	virtual void loadPostProcess() { UpdateModule::loadPostProcess(); }	// retail slot 1 0x00497805: a jmp to UpdateModule's
};
// SIZE 0x94
typedef char LargeGroupAudioUpdate_size[(sizeof(LargeGroupAudioUpdate) == 0x94) ? 1 : -1];
typedef char LargeGroupAudioUpdate_off_m_unk0x28[(offsetof(LargeGroupAudioUpdate, m_unk0x28) == 0x28) ? 1 : -1];
typedef char LargeGroupAudioUpdate_off_m_unk0x8C[(offsetof(LargeGroupAudioUpdate, m_unk0x8C) == 0x8C) ? 1 : -1];
typedef char LargeGroupAudioUpdate_off_m_unk0x8D[(offsetof(LargeGroupAudioUpdate, m_unk0x8D) == 0x8D) ? 1 : -1];
typedef char LargeGroupAudioUpdate_off_m_unk0x90[(offsetof(LargeGroupAudioUpdate, m_unk0x90) == 0x90) ? 1 : -1];

#endif
