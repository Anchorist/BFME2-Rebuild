#pragma once

#include "Common/GameType.h"
#include "Common/Snapshot.h"
#include "Common/StlList.h"
#include "GameLogic/ObjectFilter.h"

class Coord3D;
class Object;
class ScoreKeeper;

// 0x0055A998 installs table 0x0083A08C. The destructor at 0x00414520
// releases the frame list and filter and restores the Snapshot table.
class ScoredKillTracker : public Snapshot
{
public:
    ScoredKillTracker(UnsignedInt trackingDuration, const ObjectFilter &filter,
        UnsignedInt playerMask);
    ScoredKillTracker(const ScoredKillTracker &other);
    virtual ~ScoredKillTracker();

    bool rva0055A892(const Object *object);
    void friend_addTrackedKill(const Coord3D *position);
    void friend_update();
    void rva0055A91A(); // unhooks from the score keeper and clears the frame list
    void hookToKeeper(ScoreKeeper *scoreKeeper); // 0x0055A93C
    virtual const char *GetSnapshotName() const; // 0x0055A914

protected:
    virtual void loadPostProcess(); // 0x0055A962
    virtual void xfer(Xfer *xfer); // 0x0055AA68

private:
    UnsignedInt m_trackingDuration; // 0x0055AA37 adds it to each recorded frame
    ObjectFilter m_filter; // 0x0055A892 tests it and 0x0055AA68 transfers it
    UnsignedInt m_playerMask; // 0x0055A892 tests the owning player's bit
    ScoreKeeper *m_scoreKeeper; // set by 0x0055A93C and used by 0x0055A91A
    Int m_playerIndex; // 0x0055A962 uses it to reattach after loading
    _STL::list<Int> m_killFrames; // 0x0055AA06 appends the current frame and 0x0055AA37 pops expired frames
    Int m_killCount;
};

typedef char ScoredKillTrackerSize[(sizeof(ScoredKillTracker) == 0x20) ? 1 : -1];
