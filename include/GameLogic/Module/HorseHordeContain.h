#pragma once
#ifndef BFME2_HORSE_HORDE_CONTAIN_H
#define BFME2_HORSE_HORDE_CONTAIN_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/HordeContain.h"

class Thing;
class ModuleData;
class Xfer;

// Horse formations use the shared horde layout.
class HorseHordeContain : public HordeContain
{
public:
	HorseHordeContain(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual ~HorseHordeContain();
	virtual void returnToFormation(Bool flag);
	virtual void hordeSlot15();

protected:
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

};
typedef char HorseHordeContain_size[(sizeof(HorseHordeContain) == 0x30C) ? 1 : -1];

#endif
