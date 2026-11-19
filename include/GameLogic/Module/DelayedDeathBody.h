// Respawn body subclass with delayed death.
#pragma once
#ifndef BFME2_DELAYED_DEATH_BODY_H
#define BFME2_DELAYED_DEATH_BODY_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/RespawnBody.h"

class Thing;
class ModuleData;
class Xfer;

// RespawnBody ends at 0x100; this class's members follow it.
typedef char DelayedDeathBody_base_size[(sizeof(RespawnBody) == 0x100) ? 1 : -1];

class DelayedDeathBody : public RespawnBody
{
public:
	DelayedDeathBody(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual void internalChangeHealth(Real, DamageInfo *);	// override: internalChangeHealth slot 32 at +0x10 (0x004C167E)

protected:
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

public:
	Bool m_unk0x100;                               // +0x100; xfer Bool
	Bool m_unk0x101;                               // +0x101; xfer Bool
};
// SIZE 0x104
typedef char DelayedDeathBody_size[(sizeof(DelayedDeathBody) == 0x104) ? 1 : -1];
typedef char DelayedDeathBody_off_m_unk0x100[(offsetof(DelayedDeathBody, m_unk0x100) == 0x100) ? 1 : -1];
typedef char DelayedDeathBody_off_m_unk0x101[(offsetof(DelayedDeathBody, m_unk0x101) == 0x101) ? 1 : -1];

#endif
