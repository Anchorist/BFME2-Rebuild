// Respawn body subclass with a configurable additional life.
#pragma once
#ifndef BFME2_FREE_LIFE_BODY_H
#define BFME2_FREE_LIFE_BODY_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/RespawnBody.h"

class Thing;
class ModuleData;
class Xfer;

// RespawnBody ends at 0x100; this class's members follow it.
typedef char FreeLifeBody_base_size[(sizeof(RespawnBody) == 0x100) ? 1 : -1];

class FreeLifeBody : public RespawnBody
{
public:
	FreeLifeBody(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual const char *GetSnapshotName() const;

protected:
	virtual void xfer(Xfer *xfer);

public:
	Bool m_unk0x100;                               // +0x100; xfer Bool
	Real m_unk0x104;                               // +0x104; xfer Real
	Bool m_unk0x108;                               // +0x108; xfer Bool
	UnsignedInt m_unk0x10C;                        // +0x10C; xfer UnsignedInt
	UnsignedInt m_unk0x110;                        // +0x110; xfer UnsignedInt
};
// SIZE 0x114
typedef char FreeLifeBody_size[(sizeof(FreeLifeBody) == 0x114) ? 1 : -1];
typedef char FreeLifeBody_off_m_unk0x100[(offsetof(FreeLifeBody, m_unk0x100) == 0x100) ? 1 : -1];
typedef char FreeLifeBody_off_m_unk0x104[(offsetof(FreeLifeBody, m_unk0x104) == 0x104) ? 1 : -1];
typedef char FreeLifeBody_off_m_unk0x108[(offsetof(FreeLifeBody, m_unk0x108) == 0x108) ? 1 : -1];
typedef char FreeLifeBody_off_m_unk0x10C[(offsetof(FreeLifeBody, m_unk0x10C) == 0x10C) ? 1 : -1];
typedef char FreeLifeBody_off_m_unk0x110[(offsetof(FreeLifeBody, m_unk0x110) == 0x110) ? 1 : -1];

#endif
