// CritterEmitterUpdate.h: the CritterEmitterUpdate module. SIZE 0x28: UpdateModule (0x20) and the CollideModuleInterface
// table at +0x20, then two Bools that xfer saves at +0x24 and +0x25. The constructor runs UpdateModule's and installs the
// class tables. update is the +0x10 table's slot 0 and onCollide is the collide table's slot 0; the other collide queries
// answer false. xfer also makes one transfer through a slot this view cannot place.
#pragma once
#ifndef BFME2_CRITTER_EMITTER_UPDATE_H
#define BFME2_CRITTER_EMITTER_UPDATE_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/UpdateModule.h"
#include "GameLogic/Module/CollideModule.h"

class Thing;
class ModuleData;
class Xfer;

// UpdateModule ends at 0x20; this class's members follow it.
typedef char CritterEmitterUpdate_base_size[(sizeof(UpdateModule) == 0x20) ? 1 : -1];

class CritterEmitterUpdate : public UpdateModule, public CollideModuleInterface
{
public:
	virtual CollideModuleInterface *getCollide() { return this; }
	CritterEmitterUpdate(Thing *thing, const ModuleData *moduleData);
	static Module *friend_newModuleInstance(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual UpdateSleepTime update();	// override: update slot 0 at +0x10
	virtual void onCollide(Object *other, const Coord3D *loc, const Coord3D *normal);	// override: onCollide slot 0 at +0x20
	virtual Bool wouldLikeToCollideWith(const Object *) const { return false; }
	virtual Bool isHijackedVehicleCrateCollide() const { return false; }
	virtual Bool isCarBombCrateCollide() const { return false; }
	virtual Bool isRailroad() const { return false; }
	virtual Bool isSalvageCrateCollide() const { return false; }

protected:
	virtual ~CritterEmitterUpdate();
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

public:
	Bool m_unk0x24;                                // +0x24; xfer Bool
	Bool m_unk0x25;                                // +0x25; xfer Bool
protected:
	virtual void loadPostProcess() { UpdateModule::loadPostProcess(); }	// slot 1: a jump to UpdateModule's
};
// SIZE 0x28
typedef char CritterEmitterUpdate_size[(sizeof(CritterEmitterUpdate) == 0x28) ? 1 : -1];
typedef char CritterEmitterUpdate_off_m_unk0x24[(offsetof(CritterEmitterUpdate, m_unk0x24) == 0x24) ? 1 : -1];
typedef char CritterEmitterUpdate_off_m_unk0x25[(offsetof(CritterEmitterUpdate, m_unk0x25) == 0x25) ? 1 : -1];

#endif
