// The slow-death behavior that checks whether nearby geometry is clear.
#pragma once
#ifndef BFME2_CLEARANCE_TESTING_SLOW_DEATH_BEHAVIOR_H
#define BFME2_CLEARANCE_TESTING_SLOW_DEATH_BEHAVIOR_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/SlowDeathBehavior.h"

class Thing;
class ModuleData;
class Xfer;
class Coord3D;
class GeometryInfo;

// SlowDeathBehavior ends at 0x50; this class's members follow it.
typedef char ClearanceTestingSlowDeathBehavior_base_size[(sizeof(SlowDeathBehavior) == 0x50) ? 1 : -1];

// The geometry source exposed by the clearance-testing behavior.
class ClearanceTestGeometryInterface
{
public:
	virtual const GeometryInfo *getClearanceTestGeometry() const = 0;
	virtual void getClearanceTestGeometryCenter(Coord3D *center) = 0;
	virtual Real getClearanceTestGeometryAngle() const = 0;
};

class ClearanceTestingSlowDeathBehavior : public SlowDeathBehavior, public ClearanceTestGeometryInterface
{
public:
	char const * name() const;	// 0x00483C63
	ClearanceTestingSlowDeathBehavior(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual const char *GetSnapshotName() const;
	virtual ClearanceTestGeometryInterface *getClearanceTestGeometryInterface();
	virtual ClearanceTestGeometryInterface *slot24();
	virtual const GeometryInfo *getClearanceTestGeometry() const;
	virtual void getClearanceTestGeometryCenter(Coord3D *center);
	virtual Real getClearanceTestGeometryAngle() const;

protected:
	virtual void xfer(Xfer *xfer);

	virtual void loadPostProcess() { SlowDeathBehavior::loadPostProcess(); }	// retail slot 1 0x00483CEF: a jmp to SlowDeathBehavior's
};
// SIZE 0x54
typedef char ClearanceTestingSlowDeathBehavior_size[(sizeof(ClearanceTestingSlowDeathBehavior) == 0x54) ? 1 : -1];

#endif
