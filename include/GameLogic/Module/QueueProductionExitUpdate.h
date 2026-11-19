// QueueProductionExitUpdate controls the timing and rally point for produced objects.
// getRallyPoint 0x004A001D reads the valid flag at +0x34 and returns the
// coordinate at +0x28. setRallyPoint 0x004A051B writes both members.
#pragma once
#ifndef BFME2_QUEUE_PRODUCTION_EXIT_UPDATE_H
#define BFME2_QUEUE_PRODUCTION_EXIT_UPDATE_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/UpdateModule.h"
#include "GameLogic/Module/ExitInterface.h"
#include "Common/Coord3D.h"

class Thing;
class ModuleData;
class Xfer;

// UpdateModule ends at 0x20; this class's members follow it.
typedef char QueueProductionExitUpdate_base_size[(sizeof(UpdateModule) == 0x20) ? 1 : -1];

class QueueProductionExitUpdate : public UpdateModule, public ExitInterface
{
public:
	virtual ExitInterface *getUpdateExitInterface() { return this; }
	QueueProductionExitUpdate(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual const char *GetSnapshotName() const;
	const char *name() const;   // 0x004A0017, non-virtual name getter (QBE)
	// ExitInterface slot 8 (+0x20): retail 0x004A001D tests [this+0x14] and returns this+8, i.e.
	// m_hasRallyPoint and &m_rallyPoint seen from the interface sub-object.
	virtual const Coord3D *getRallyPoint() const;
	virtual void setRallyPoint(const Coord3D *position);
	virtual ExitDoorType reserveDoorForExit(const ThingTemplate *, Object *);	// 0x004A0268: EXIT_DOOR_FIRST when isFreeToExit, else EXIT_DOOR_NONE	// 0x004A051B: rally override or the given point into m_rallyPoint, then m_hasRallyPoint = true
	virtual Bool getExitPosition(Coord3D &exitPosition, Real &exitAngle) const;	// ExitInterface slot 10: 0x004A0194 (transform of the module's exit point)
	virtual UpdateSleepTime update();						// 0x004A003C: frees the delay counter once the exit is free, otherwise counts it down

protected:
	virtual void xfer(Xfer *xfer);
	virtual ~QueueProductionExitUpdate();

public:
	UnsignedInt m_currentDelay;                     // +0x24; xfer UnsignedInt; isFreeToExit 0x004A002A reads it
	Coord3D m_rallyPoint;                             // +0x28; xfer Coord3D
	Bool m_hasRallyPoint;                                // +0x34; xfer Bool
	Real m_unk0x38;                                // +0x38; xfer Real
	UnsignedInt m_currentBurstCount;               // +0x3C; xfer UnsignedInt; isFreeToExit 0x004A002A reads it
	ObjectID m_unk0x40;                            // +0x40; xfer ObjectID
protected:
	bool isFreeToExit() const; // 0x004A002A (IBE: protected)
public:
protected:
	virtual void loadPostProcess() { UpdateModule::loadPostProcess(); }	// retail slot 0x00497805: a jmp to UpdateModule's, ICF-folded across classes
public:
	virtual Bool useSpawnRallyPoint() const;	// ExitInterface slot 6: 0x004A0107 (`mov al,[ecx+0x14]`: the rally point exists)
	virtual Bool isExitBusy() const { return false; }	// ExitInterface slot 0: retail 0x0047A699, `xor al,al; ret` (ICF-folded)
	// The ExitInterface slots come from retail table 0x0085198C.
	virtual void exitObjectViaDoor(Object *newObj, ExitDoorType exitDoor);	// slot 2: 0x004A0709
	virtual void exitObjectByBudding(Object *newObj, Object *budHost);		// slot 3: 0x004A0670
	virtual void unreserveDoorForExit(ExitDoorType exitDoor) {}				// slot 4: 0x0047A69C (ICF-folded `ret 4`)
	virtual Bool getNaturalRallyPoint(Coord3D &rallyPoint, Bool offset) const;	// slot 9: 0x004A027A
	virtual void notifyProductionBurstFinished();								// slot 11: 0x004A0547 (the map spells it QAE, non-virtual)
	// slot 6 (useSpawnRallyPoint) is 0x004A0107, which the map files as ?get@Rva004A0107ByteChaseField: not declared until it is named
};
// SIZE 0x44
typedef char QueueProductionExitUpdate_size[(sizeof(QueueProductionExitUpdate) == 0x44) ? 1 : -1];
typedef char QueueProductionExitUpdate_off_m_currentDelay[(offsetof(QueueProductionExitUpdate, m_currentDelay) == 0x24) ? 1 : -1];
typedef char QueueProductionExitUpdate_off_m_rallyPoint[(offsetof(QueueProductionExitUpdate, m_rallyPoint) == 0x28) ? 1 : -1];
typedef char QueueProductionExitUpdate_off_m_hasRallyPoint[(offsetof(QueueProductionExitUpdate, m_hasRallyPoint) == 0x34) ? 1 : -1];
typedef char QueueProductionExitUpdate_off_m_unk0x38[(offsetof(QueueProductionExitUpdate, m_unk0x38) == 0x38) ? 1 : -1];
typedef char QueueProductionExitUpdate_off_m_currentBurstCount[(offsetof(QueueProductionExitUpdate, m_currentBurstCount) == 0x3C) ? 1 : -1];
typedef char QueueProductionExitUpdate_off_m_unk0x40[(offsetof(QueueProductionExitUpdate, m_unk0x40) == 0x40) ? 1 : -1];

#endif
