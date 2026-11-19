// An active body that retains the immortal module behavior.
#pragma once
#ifndef BFME2_IMMORTAL_BODY_H
#define BFME2_IMMORTAL_BODY_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/ActiveBody.h"

class Thing;
class ModuleData;
class Xfer;
struct DamageInfo;

// ActiveBody ends at 0x100; this class's members follow it.
typedef char ImmortalBody_base_size[(sizeof(ActiveBody) == 0x100) ? 1 : -1];

class ImmortalBody : public ActiveBody
{
public:
	ImmortalBody(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual void internalChangeHealth(Real amount, DamageInfo *damageInfo);	// 0x004C0918 (+0x10 slot 32)

protected:
	virtual void loadPostProcess() { ActiveBody::loadPostProcess(); }	// slot 1: retail 0x004C202F, a jmp to ActiveBody's (0x004BF40F), ICF-folded across the ActiveBody subclasses
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

public:
};
// SIZE 0x100
typedef char ImmortalBody_size[(sizeof(ImmortalBody) == 0x100) ? 1 : -1];

#endif
