// LargeGroupAudioUpdate.h: the LargeGroupAudioUpdate module. SIZE 0x94 (ModuleFactory operator new).
// Target facts: the constructor 0x004AB811 calls UpdateModule first; it stores the
// tables 0x00C6FFFC at +0x20, 0x00BFB698 at +0x24, 0x00C549BC at +0x0, 0x00C54900 at +0xC, 0x00C548F0 at +0x10, 0x00C548E8 at +0x20, 0x00C548B8 at +0x24. Members are what xfer (0x004AB9EA) transfers after UpdateModule::xfer,
// typed by the Xfer slot each goes through, in that order; m_unk names are offsets
// (no map or donor name established). Bytes xfer does not touch are gaps.
// Not established: interface tables at +0x20, +0x24 (their vptrs sit in the gaps there).
// Not established: transfers xfer makes that this view cannot place: slot10 ?, ?xfer@?$BitFlags@$0CEP@@@QAEXPAVXfer@@@Z +0x30, ?xfer@?$BitFlags@$0GF@@@QAEXPAVXfer@@@Z +0x7C.
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
	void rva004AB90A();	// 0x004AB90A (onObjectCreated calls it unless +0x8D is set)
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
