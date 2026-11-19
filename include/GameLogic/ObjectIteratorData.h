#pragma once

#include "GameLogic/ObjectIteratorEntry.h"
#include <vector>

struct ObjectIteratorData
{
    _STL::vector<ObjectIteratorEntry> m_objects; // +0x00, destroyed by 0x0007FAB3
    ObjectIteratorEntry *m_cursor;               // +0x0C, 0x00045623 advances it eight bytes
    int m_referenceCount;                       // +0x10, decremented by 0x0004AA28
};

typedef char ObjectIteratorDataSize[(sizeof(ObjectIteratorData) == 0x14) ? 1 : -1];
