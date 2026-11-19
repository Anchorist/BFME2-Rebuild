#pragma once

#include <stddef.h>

#include "Common/AsciiString.h"
#include "Common/Coord3D.h"

#pragma pack(push, 1)
class Waypoint
{
public:
	virtual ~Waypoint();

	unsigned int getID() const { return m_id; }
	void addLink(Waypoint *way);
	Waypoint *getLink(Int index) const
	{
		if (index < 0 || index >= 8)
			return 0;
		return m_links[index];
	}
	AsciiString getPathLabel1() const;
	AsciiString getPathLabel2() const;
	AsciiString getPathLabel3() const;

	unsigned int m_id;
	AsciiString m_name;
	Coord3D m_location;
	Waypoint *m_prev;
	Waypoint *m_next;
	Waypoint *m_links[8];
	// addLink records the waypoint that linked to this one.
	Waypoint *m_owner;
	Int m_unk0x44;
	Bool m_unk0x48;
	unsigned char m_pad0x49[3];
	Int m_numLinks;
	AsciiString m_pathLabel1;
	AsciiString m_pathLabel2;
	AsciiString m_pathLabel3;
	Bool m_biDirectional;
	unsigned char m_pad0x5D[3];
	// ScriptActions::doMoveCameraAlongWaypointPath requires path type 6.
	Int m_pathType;
	AsciiString m_unk0x64;
	Bool m_unk0x68;
	unsigned char m_pad0x69[3];
	unsigned char m_unk0x6C[0x1C];
	Bool m_unk0x88;
	unsigned char m_pad0x89[3];
	unsigned char m_unk0x8C[0x1C];
	Bool m_unk0xA8;
	Bool m_unk0xA9;
	unsigned char m_pad0xAA[2];
	Int m_unk0xAC;
	Int m_unk0xB0;
	Int m_unk0xB4;
	Bool m_unk0xB8;
	unsigned char m_pad0xB9[3];
	unsigned char m_unk0xBC[4];
};
#pragma pack(pop)

typedef char WaypointOffsets[(offsetof(Waypoint, m_numLinks) == 0x4C &&
	offsetof(Waypoint, m_pathLabel3) == 0x58 && offsetof(Waypoint, m_pathType) == 0x60 &&
	offsetof(Waypoint, m_unk0xAC) == 0xAC && offsetof(Waypoint, m_unk0xBC) == 0xBC)
	? 1 : -1];
