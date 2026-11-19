// Portions derived from Command & Conquer Generals and Command & Conquer Generals Zero Hour, (c) Electronic Arts Inc., GPL-3.0-or-later; see LICENSE and NOTICE.
// 0x00062A7E constructs TerrainLogic and installs the W3D Snapshot and
// SubsystemInterface tables. The two AreaSetObserver tables are inherited.
#pragma once

#include "GameLogic/TerrainLogic.h"

class W3DTerrainLogic : public TerrainLogic
{
public:
	W3DTerrainLogic();
	virtual ~W3DTerrainLogic();

	virtual void init();
	virtual void reset();
	virtual void update();

	virtual Bool loadMap(const AsciiString &filename, ChunkInputStream *stream,
		Bool, Bool);
	virtual void newMap(Bool saveGame);
	virtual Real getGroundHeight(Real x, Real y, Coord3D *normal = 0) const;
	virtual Real getLayerHeight(Real x, Real y, PathfindLayerEnum layer,
		Coord3D *normal = 0, Bool clip = true) const;

	virtual void activeBoundaryExtent(Region3D *extent) const;
	virtual void largestBoundaryExtent(Region3D *extent) const;
	virtual void getExtentIncludingBorder(Region3D *extent) const;
	virtual Real rva00062E4F();
	virtual void getMaximumPathfindExtent(Region3D *extent) const;
	virtual Bool isClearLineOfSight(const Coord3D &start, const Coord3D &end) const;
	virtual Real getHighestHeight(const Coord3D *start, const Coord3D *end) const;

	virtual Bool isCliffCell(Real x, Real y) const;
	virtual UnsignedByte rva00062DB3(Real x, Real y) const;
	virtual UnsignedByte rva00062DD2(Real x, Real y) const;
	virtual Bool rva00062DF1(Real x, Real y) const;
	virtual UnsignedByte rva00062E10(Real x, Real y) const;
	virtual Bool rva00063082(const Coord3D *pos) const;

protected:
	virtual void loadPostProcess();
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

	// The loadMap scan at 0x63258..0x632AB scales the minimum and maximum
	// sampled heights into these two world-coordinate bounds.
	Real m_mapMinZ;
	Real m_mapMaxZ;
};

typedef char W3DTerrainLogicSize[(sizeof(W3DTerrainLogic) == 0x1924) ? 1 : -1];
