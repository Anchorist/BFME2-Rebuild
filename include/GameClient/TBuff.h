#pragma once

#include "Common/Coord3D.h"
#include "Common/GameType.h"
#include "Common/Snapshot.h"

class BuffInstance;
class Drawable;

// W3DBuffBuffer::addBuff allocates 0x58 bytes at 0x000D3BB5 and constructs
// this Snapshot at 0x000D1AF3. Its four-slot table is at RVA 0x007CE310.
class TBuff : public Snapshot
{
	friend class BuffInstance;

public:
	TBuff(const Drawable *drawable, Int typeIndex);	// 0x000D1AF3
	virtual ~TBuff();	// 0x000D1BA6, deleting 0x000D208D
	void release();	// 0x00419BA5, shared virtual destruction and deallocation

protected:
	virtual void loadPostProcess() {}	// slot 1, empty 0x000B3FD0
	virtual const char *GetSnapshotName() const;	// 0x000D1BA0
	virtual void xfer(Xfer *xfer);	// 0x000D211D

private:
	// 0x000D1C10 raises intensity in FADING_IN and lowers it in FADING_OUT.
	enum FadeState
	{
		FADING_IN = 0,
		ACTIVE = 1,
		FADING_OUT = 2,
		INACTIVE = 3
	};

	Int m_typeIndex;	// +0x04, addBuff passes the registered type index
	FadeState m_state;	// +0x08, updated by 0x000D1C10
	Real m_intensity;	// +0x0C, changed alongside the fade state
	Bool m_unk0x10;
	UnsignedByte m_unk0x11[3];
	UnsignedByte m_unk0x14[0x30];	// 0x000D1B33 constructs three 16-byte records
	Bool m_unk0x44;	// ctor copies Drawable +0x441; xfer transfers Bool
	Bool m_unk0x45;
	Coord3D m_position;	// +0x48, from Drawable::getPosition in 0x000D1B7D
	Real m_instanceScale;	// +0x54, from Drawable +0x200 at 0x000D1B73
};

typedef char TBuff_size[(sizeof(TBuff) == 0x58) ? 1 : -1];
