// Portions derived from Command & Conquer Generals and Command & Conquer Generals Zero Hour, (c) Electronic Arts Inc., GPL-3.0-or-later; see LICENSE and NOTICE.
// The native constructor 0x00305A8F builds Snapshot at +0 and ShroudGhostClient
// at +4. The inherited virtual ShroudClient is at +0x84 in a complete
// GhostObject, addressed through the vbtable at 0x00807950.
#pragma once

#include "Common/Coord3D.h"
#include "Common/Geometry.h"
#include "Common/Snapshot.h"
#include "shroudmanager/ShroudGhostClient.h"

class Object;

class GhostObject : public Snapshot, public ShroudGhostClient
{
public:
	GhostObject();
	virtual ~GhostObject();

	virtual GhostObject *getNextGhostObject() const = 0;

	virtual const GeometryInfo *ShroudGetGeometryInfo() const;
	virtual const Coord3D *ShroudGetPosition() const;
	virtual Real ShroudGetOrientation() const;
	virtual void ShroudSetData(PartitionData *data);
	virtual PartitionData *ShroudGetData() const;

protected:
	virtual void loadPostProcess();
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

	Object *m_parentObject;
	Coord3D m_parentPosition;
	Real m_parentAngle;
	GeometryInfo m_parentGeometry;
	PartitionData *m_partitionData;
};

typedef char GhostObjectSize[(sizeof(GhostObject) == 0x88) ? 1 : -1];
