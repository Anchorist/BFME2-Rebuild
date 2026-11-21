// The SupplyCenter exit has the native UpdateModule and ExitInterface bases.
// Its 0x34-byte layout stores the rally point and availability byte at +0x24/+0x30.
// Retail 0x4A65AE constructs both, and Exit table 0x852D00 slots 7/8 access them.
// The donor's rally field and accessors agree with those references.
#pragma once
#ifndef BFME2_SUPPLY_CENTER_PRODUCTION_EXIT_UPDATE_H
#define BFME2_SUPPLY_CENTER_PRODUCTION_EXIT_UPDATE_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/UpdateModule.h"
#include "GameLogic/Module/ExitInterface.h"
#include "Common/Coord3D.h"

class Coord3D;
class Thing;
class ModuleData;
class Xfer;

// UpdateModule ends at 0x20; this class's members follow it.
typedef char SupplyCenterProductionExitUpdate_base_size[(sizeof(UpdateModule) == 0x20) ? 1 : -1];

class SupplyCenterProductionExitUpdate : public UpdateModule, public ExitInterface
{
public:
	SupplyCenterProductionExitUpdate(Thing *thing, const ModuleData *moduleData);
	static Module *friend_newModuleInstance(Thing *thing, const ModuleData *moduleData);
	virtual ~SupplyCenterProductionExitUpdate();
	virtual NameKeyType getModuleNameKey() const;
	virtual const char *GetSnapshotName() const;
	virtual ExitInterface *getUpdateExitInterface() { return this; }
	virtual UpdateSleepTime update() { return UPDATE_SLEEP_FOREVER; }

	virtual Bool isExitBusy() const { return false; }
	virtual ExitDoorType reserveDoorForExit(const ThingTemplate *, Object *) { return EXIT_DOOR_FIRST; }
	virtual void exitObjectViaDoor(Object *newObj, ExitDoorType exitDoor);
	virtual void exitObjectByBudding(Object *, Object *) {}
	virtual void unreserveDoorForExit(ExitDoorType) {}
	virtual void setRallyPoint(const Coord3D *position);
	virtual const Coord3D *getRallyPoint() const;
	virtual Bool getNaturalRallyPoint(Coord3D &position, Bool offset) const;
	virtual Bool getExitPosition(Coord3D &exitPosition) const;

protected:
	virtual void xfer(Xfer *xfer);
	virtual void loadPostProcess() { UpdateModule::loadPostProcess(); }

private:
	Coord3D m_rallyPoint;         // +0x24
	Bool m_rallyPointExists;      // +0x30
};
typedef char SupplyCenterProductionExitUpdate_size[(sizeof(SupplyCenterProductionExitUpdate) == 0x34) ? 1 : -1];

inline void SupplyCenterProductionExitUpdate::setRallyPoint(const Coord3D *position)
{
	m_rallyPoint = *position;
	m_rallyPointExists = true;
}

inline const Coord3D *SupplyCenterProductionExitUpdate::getRallyPoint() const
{
	if (m_rallyPointExists)
		return &m_rallyPoint;
	return 0;
}

#endif
