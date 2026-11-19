// Portions derived from Command & Conquer Generals and Command & Conquer Generals Zero Hour, (c) Electronic Arts Inc., GPL-3.0-or-later; see LICENSE and NOTICE.
// 0x00063517 installs the renderer manager's table 0x007C59B8 and
// clears the two list heads following the GhostObjectManager base.
#pragma once

#include "GameLogic/GhostObjectManager.h"

class W3DGhostObject;

class W3DGhostObjectManager : public GhostObjectManager
{
public:
	W3DGhostObjectManager();
	virtual ~W3DGhostObjectManager();

	virtual void reset();
	virtual void setLocalPlayerIndex(Int index);
	virtual void updateOrphanedObjects(Int *playerIndexList, Int numNonLocalPlayers);
	virtual GhostObject *addGhostObject(Object *object);
	virtual GhostObject *getFirstGhostObject() const;

	void removeGhostObject(GhostObject *ghost);

protected:
	virtual void loadPostProcess();
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

	W3DGhostObject *m_freeModules;
	W3DGhostObject *m_usedModules;
};

typedef char W3DGhostObjectManagerSize[(sizeof(W3DGhostObjectManager) == 0x14) ? 1 : -1];
