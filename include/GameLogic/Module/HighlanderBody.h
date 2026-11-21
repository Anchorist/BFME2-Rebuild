// An active body with the highlander death rules.
#pragma once
#ifndef BFME2_HIGHLANDER_BODY_H
#define BFME2_HIGHLANDER_BODY_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/ActiveBody.h"

class Thing;
class ModuleData;
class Xfer;
struct DamageInfo;

// ActiveBody ends at 0x100; this class's members follow it.
typedef char HighlanderBody_base_size[(sizeof(ActiveBody) == 0x100) ? 1 : -1];

class HighlanderBody : public ActiveBody
{
public:
	HighlanderBody(Thing *thing, const ModuleData *moduleData);
	static Module *friend_newModuleInstance(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual ~HighlanderBody();
	virtual void attemptDamage(DamageInfo *damageInfo);		// (+0x10 slot 0)

protected:
	virtual void loadPostProcess() { ActiveBody::loadPostProcess(); }	// slot 1: retail 0x004C202F, a jmp to ActiveBody's (0x004BF40F), ICF-folded across the ActiveBody subclasses
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

public:
};
// SIZE 0x100
typedef char HighlanderBody_size[(sizeof(HighlanderBody) == 0x100) ? 1 : -1];

#endif
