// Portions derived from Command & Conquer Generals and Command & Conquer Generals Zero Hour, (c) Electronic Arts Inc., GPL-3.0-or-later; see LICENSE and NOTICE.
// 0x00063912 installs the Snapshot and ShroudGhostClient tables 0x007C5994
// and 0x007C5984. The vbtable moves the inherited ShroudClient to +0xEC.
#pragma once

#include "Common/PlayerList.h"
#include "GameClient/DrawableInfo.h"
#include "GameLogic/GhostObject.h"

class W3DGhostObjectManager;
class W3DRenderObjectSnapshot;

class W3DGhostObject : public GhostObject
{
	friend class W3DGhostObjectManager;

public:
	W3DGhostObject();
	virtual ~W3DGhostObject();

	virtual GhostObject *getNextGhostObject() const;
	virtual void vslot00();
	virtual void vslot01();
	virtual void snapShot(Int playerIndex);
	virtual void freeSnapShot(Int playerIndex);

protected:
	virtual void loadPostProcess();
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

	void removeParentObject();
	void restoreParentObject();
	void removeFromScene(Int playerIndex);
	void addToScene(Int playerIndex);
	void getShroudStatus(Int playerIndex);
	void freeAllSnapShots();

	W3DRenderObjectSnapshot *m_parentSnapshots[MAX_PLAYER_COUNT];
	DrawableInfo m_drawableInfo;
	W3DGhostObject *m_nextSystem;
	W3DGhostObject *m_prevSystem;
};

typedef char W3DGhostObjectSize[(sizeof(W3DGhostObject) == 0xF0) ? 1 : -1];
