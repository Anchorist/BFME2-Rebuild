#pragma once

#include "Common/Snapshot.h"
#include "Common/SubsystemInterface.h"

struct BfmePointFC;
class TaintManagerImpl;

// Construction initializes the subsystem, the snapshot base, and the grid implementation.
class BfmeTaintManager : public SubsystemInterface, public Snapshot
{
public:
	BfmeTaintManager();
	virtual ~BfmeTaintManager();

	virtual void init();
	// The native reset slot dispatches the virtual initialization slot.
	virtual void reset() { init(); }
	virtual void update();

	void rva006C0800(void (*callback)(int, int, int));
	void bfmeApplyCircleWorld(const BfmePointFC *center, float radius, int strength,
		bool flag, int objectID);

protected:
	virtual void loadPostProcess() {}
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

private:
	// Allocated by the constructor and used by the taint-grid forwards.
	TaintManagerImpl *m_impl;
};

// The game-engine initializer allocates this extent before calling the constructor.
typedef char BfmeTaintManagerSizeCheck[sizeof(BfmeTaintManager) == 0x14 ? 1 : -1];

extern BfmeTaintManager *TheTaintManager;
