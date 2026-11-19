// RespawnBody delegates its usual damage behavior to ActiveBody and overrides health changes.
#pragma once
#ifndef BFME2_RESPAWN_BODY_H
#define BFME2_RESPAWN_BODY_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/ActiveBody.h"

class Thing;
class ModuleData;
class Xfer;

// ActiveBody ends at 0x100; this class's members follow it.
typedef char RespawnBody_base_size[(sizeof(ActiveBody) == 0x100) ? 1 : -1];

class RespawnBody : public ActiveBody
{
public:
	RespawnBody(Thing *thing, const ModuleData *moduleData);
	virtual ~RespawnBody();
	virtual NameKeyType getModuleNameKey() const;
	virtual void internalChangeHealth(Real, DamageInfo *);	// override: internalChangeHealth slot 32 at +0x10 (0x004C1395)

protected:
	virtual void loadPostProcess() { ActiveBody::loadPostProcess(); }
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

public:
};
// SIZE 0x100
typedef char RespawnBody_size[(sizeof(RespawnBody) == 0x100) ? 1 : -1];

#endif
