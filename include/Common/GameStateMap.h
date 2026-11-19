#pragma once
#include "Common/SubsystemInterface.h"
#include "Common/Snapshot.h"
// Constructor 0x0041AC6A installs SubsystemInterface at +0 with
// table 0x0083ADD8 and Snapshot at +0x0C with table 0x0083ADC8.
// Destructor 0x0041B790 restores both tables before clearing scratch-pad maps.
// The transfer helpers use shared save state.
class GameStateMap : public SubsystemInterface, public Snapshot
{
public:
    GameStateMap();
    virtual ~GameStateMap();
    virtual void init();
    virtual void reset();
    virtual void update();
    virtual const char *GetSnapshotName() const;
    void DoXfer(Xfer *xfer);
    void clearScratchPadMaps();
protected:
    virtual void loadPostProcess();
    virtual void xfer(Xfer *xfer);
};
