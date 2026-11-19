// Portions derived from Command & Conquer Generals and Command & Conquer Generals Zero Hour, (c) Electronic Arts Inc., GPL-3.0-or-later; see LICENSE and NOTICE.
// The constructor 0x00063861 stores the Snapshot table at 0x007C59F4 and
// clears the render object and next-snapshot pointers. The destructor
// 0x000638C4 detaches and releases the render object, then restores the base table.
#pragma once

#include "Common/GameType.h"
#include "Common/Snapshot.h"

struct DrawableInfo;
class RenderObjClass;
class W3DGhostObject;

class W3DRenderObjectSnapshot : public Snapshot
{
	friend class W3DGhostObject;

	W3DRenderObjectSnapshot(RenderObjClass *parent, DrawableInfo *drawInfo, Bool cloneParent);
	virtual ~W3DRenderObjectSnapshot();

	void update(RenderObjClass *parent, DrawableInfo *drawInfo, Bool cloneParent);

protected:
	virtual void loadPostProcess();
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

	RenderObjClass *m_robj;
	W3DRenderObjectSnapshot *m_next;
};

typedef char W3DRenderObjectSnapshotSize[(sizeof(W3DRenderObjectSnapshot) == 0xC) ? 1 : -1];
