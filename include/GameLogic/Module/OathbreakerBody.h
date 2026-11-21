// The active-body subclass for oathbreaker objects.
#pragma once
#ifndef BFME2_OATHBREAKER_BODY_H
#define BFME2_OATHBREAKER_BODY_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/ActiveBody.h"

class Thing;
class ModuleData;
class Xfer;

// ActiveBody ends at 0x100; this class's members follow it.
typedef char OathbreakerBody_base_size[(sizeof(ActiveBody) == 0x100) ? 1 : -1];

class OathbreakerBody : public ActiveBody
{
public:
	OathbreakerBody(Thing *thing, const ModuleData *moduleData);
	static Module *friend_newModuleInstance(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual ~OathbreakerBody();
	virtual void attemptDamage(DamageInfo *);	// override: attemptDamage slot 0 at +0x10 (0x004C1F71)

protected:
	virtual void loadPostProcess() { ActiveBody::loadPostProcess(); }	// slot 1: retail 0x004C202F, a jmp to ActiveBody's (0x004BF40F), ICF-folded across the ActiveBody subclasses
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

public:
};
// SIZE 0x100
typedef char OathbreakerBody_size[(sizeof(OathbreakerBody) == 0x100) ? 1 : -1];

#endif
