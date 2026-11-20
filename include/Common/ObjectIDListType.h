#pragma once

#include "Common/FreelistPool.h"
#include "Common/GameType.h"
#include "Common/StlList.h"

// The layout declaration is usable by classes that embed the list. Files
// that call the retail erase specialization include Common/ObjectIDList.h.
typedef _STL::list<ObjectID, FreelistAllocator<ObjectID> > ObjectIDList;
typedef ObjectIDList::iterator ObjectIDListIterator;
typedef ObjectIDList::const_iterator ObjectIDListConstIterator;
