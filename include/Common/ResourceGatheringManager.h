#pragma once

#include <list>

#include "Common/Coord3D.h"
#include "Common/GameType.h"
#include "Common/Snapshot.h"

class Object;

class ResourceGatheringManager : public Snapshot
{
public:
	ResourceGatheringManager();
	virtual ~ResourceGatheringManager();

	void rva004F5C44(Object *center);
	void addSupplyWarehouse(Object *warehouse);
	Object *findBestSupplyCenter(Object *truck);
	Object *findBestSupplyWarehouse(Object *truck);
	// Reports a tree-harvesting position for the truck.
	Bool rva004F5A67(Object *truck, Coord3D *position);
	void removeSupplyCenter(Object *center);
	void removeSupplyWarehouse(Object *warehouse);

protected:
	virtual void loadPostProcess() {}
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

private:
	// Supply creation stores Object::getID() and xfer transfers each as ObjectID.
	_STL::list<ObjectID> m_supplyWarehouses;
	_STL::list<ObjectID> m_supplyCenters;
};
