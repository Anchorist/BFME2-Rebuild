#pragma once

#include "Common/AsciiString.h"
#include "Common/Coord2D.h"
#include "Common/Snapshot.h"
#include "Common/Vector.h"

// Native constructor 0x003F24F3 installs the four-slot Snapshot table
// 0x00836E48. Destructor 0x003F2517 restores the Snapshot base table.
// The INI table at 0x00836FD4 parses Region and DetourPoint into the
// name and vector. The 0x003F2C0C transfer uses Xfer's Coord2D slot.
class LivingWorldRegionConnection : public Snapshot
{
public:
	LivingWorldRegionConnection();	// 0x003F24F3
	LivingWorldRegionConnection(const LivingWorldRegionConnection &other);	// 0x003F247D
	virtual ~LivingWorldRegionConnection();	// 0x003F2517, deleting 0x003F2A70

protected:
	virtual void loadPostProcess() {}	// slot 1, 0x000B3FD0
	virtual const char *GetSnapshotName() const;	// slot 2, 0x003F24D0
	virtual void xfer(Xfer *xfer);	// slot 3, 0x003F3054

private:
	AsciiString m_regionName;	// +0x04, INI Region
	int m_destinationRegionID;	// +0x08, xfer transfers LivingWorldRegionID
	_STL::vector<Coord2D> m_detourPoints;	// +0x0C, INI DetourPoint
};

typedef char LivingWorldRegionConnection_size[(sizeof(LivingWorldRegionConnection) == 0x18) ? 1 : -1];
