// All engine vector declarations use the vendored STLport container.
#pragma once
#ifndef BFME2_VECTOR_H
#define BFME2_VECTOR_H

#include <vector>
#include "Common/GameType.h"
#include "Common/StlAllocator.h"

namespace _STL
{
typedef vector<bool> bit_vector;
}

#endif
