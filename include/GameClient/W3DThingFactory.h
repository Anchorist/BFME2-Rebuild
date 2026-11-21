// W3DThingFactory.h: the thing factory the W3D build creates.
//
// Target facts (retail game.dat 1.06; RVAs, table addresses are VAs):
//  - Constructor 0x0004CA01 runs ThingFactory's constructor (0x002D0E14), then stores its own table (VA 0x00BC4858)
//    and returns this; the destructor 0x0004CA13 stores the table again and jumps to ThingFactory's destructor
//    (0x002D0588); the deleting destructor is 0x0004CA1E.
//  - The table repeats ThingFactory's own overrides (slots 4, 5 and 11: 0x002CF172, 0x002CEF14, 0x002CEF6C), so the class
//    adds no members and no virtuals of its own that are recovered here. The allocation size is not recovered.
#pragma once
#ifndef BFME2_W3DTHINGFACTORY_H
#define BFME2_W3DTHINGFACTORY_H

#include "Common/ThingFactory.h"

class W3DThingFactory : public ThingFactory
{
public:
	W3DThingFactory();											// 0x0004CA01
	virtual ~W3DThingFactory();									// 0x0004CA13 (deleting 0x0004CA1E)
};

#endif
