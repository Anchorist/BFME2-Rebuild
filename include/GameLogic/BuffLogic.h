#pragma once

#include "Common/Snapshot.h"
#include "Common/SubsystemInterface.h"
#include "Common/Xfer.h"

class Drawable;
class TBuff;
class ThingTemplate;

// The native constructor 0x00306782 installs Snapshot at +0 and
// SubsystemInterface at +4. W3DBuffLogic installs the leaf tables after
// calling it at 0x000647B8. BuffLogic has no fields of its own.
class BuffLogic : public Snapshot, public SubsystemInterface
{
public:
	BuffLogic();	// 0x00306782
	virtual ~BuffLogic();	// 0x003067D2
	virtual void init() {}	// subsystem slot 1, 0x000B3FD0
	virtual void reset() {}	// subsystem slot 9, 0x000B3FD0
	virtual void update() {}	// subsystem slot 10, 0x000B3FD0

	TBuff *addBuff(const ThingTemplate *buffTemplate, Drawable *drawable);	// 0x0030682A

protected:
	virtual void loadPostProcess() {}	// Snapshot slot 1, 0x000B3FD0
	virtual const char *GetSnapshotName() const;	// 0x003067C4
	virtual void xfer(Xfer *xfer) { if (!xfer->IsLightCRC()) xfer->Version1(); }	// 0x00341E2D
};

typedef char BuffLogic_size[(sizeof(BuffLogic) == 0x10) ? 1 : -1];

extern BuffLogic *TheBuffLogic;
