#pragma once
#ifndef BFME2_AIFLANKATTACKTACTICIMP_H
#define BFME2_AIFLANKATTACKTACTICIMP_H

#include "Common/Coord3D.h"
#include "Common/GameType.h"
#include "Common/Vector.h"

class Xfer;

class AIFlankAttackTacticImp
{
public:
    void DoXfer(Xfer *xfer);

    // 0x005AA0CA consumes and increments this index as it fetches the next path point.
    UnsignedInt m_nextWaypoint;

    // 0x005AA4C1 serializes these as three-float coordinates, stepping 12 bytes at a time.
    _STL::vector<Coord3D> m_waypoints;
};

// AIFlankAttackTactic allocates 0x10 bytes for its implementation at 0x005AA280.
typedef char AIFlankAttackTacticImpSize[(sizeof(AIFlankAttackTacticImp) == 0x10) ? 1 : -1];

#endif
