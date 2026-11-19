// PathNode, one node of a path. Native layout:
// - Ctor 0x0026212A (const Coord3D *pos, PathfindLayerEnum layer): zero +0/+4/+8,
//   the position at +0xC, the layer at +0x18, false at +0x1C, 0x7FFFFFFF at +0x20.
// - 0x00262161 (map placeholder Rva0026E4A0::set) is Zero Hour's prependToList:
//   +8 = list, +0 = list, list->+4 = this, returns this.
// - The pool at 0x00E01E94 grows 0x1200 bytes at a time in 128 cells of 0x24 bytes (0x002635EC through 0x0026362E).
// - Path::DoXfer 0x003661FC transfers each node's position (+0xC), layer (+0x18),
//   Bool +0x1C and the IDs of the +8 / +0x20 neighbours.
// Zero Hour PathNode names; +0 and +8 roles follow prependToList.
#pragma once
#ifndef BFME2_PATHNODE_H
#define BFME2_PATHNODE_H

#include <stddef.h>
#include "Common/GameType.h"
#include "Common/Coord3D.h"

enum PathfindLayerEnum;

class PathNode
{
public:
  const Coord3D *getPosition() const { return &m_pos; } // inline (Zero Hour's): the move-away states copy +0x0C
	PathNode(const Coord3D *pos, PathfindLayerEnum layer);	// 0x0026212A
	PathNode *prependToList(PathNode *list);				// 0x00262161

	PathNode *m_nextOpti;						// +0x00
	PathNode *m_prev;							// +0x04
	PathNode *m_next;							// +0x08
	Coord3D m_pos;								// +0x0C
	PathfindLayerEnum m_layer;					// +0x18
	Bool m_canOptimize;							// +0x1C
	Int m_id;									// +0x20, 0x7FFFFFFF
};

typedef char PathNodeSizeCheck[sizeof(PathNode) == 0x24 ? 1 : -1];
typedef char PathNodeIDOffsetCheck[offsetof(PathNode, m_id) == 0x20 ? 1 : -1];

#endif
