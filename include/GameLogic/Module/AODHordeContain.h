#pragma once
#ifndef BFME2_A_O_D_HORDE_CONTAIN_H
#define BFME2_A_O_D_HORDE_CONTAIN_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/HordeContain.h"
#include "Common/Coord3D.h"

class Thing;
class ModuleData;
class Xfer;

// The tracked-unit snapshot extends the shared horde layout.
typedef char AODHordeContain_base_size[(sizeof(HordeContain) == 0x30C) ? 1 : -1];

class AODHordeContain : public HordeContain
{
public:
	AODHordeContain(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual ~AODHordeContain();

protected:
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

public:
	void refreshTrackedLargeUnit();
	UnsignedByte m_gap0x30C[0xC];
	ObjectID m_unk0x318;
	UnsignedInt m_unk0x31C;                        // +0x31C; xfer UnsignedInt
	Coord3D m_unk0x320;                            // +0x320; xfer Coord3D
	Real m_unk0x32C;
	Real m_unk0x330;
	Real m_unk0x334;                               // +0x334; xfer Real
	UnsignedByte m_gap0x338[0x5A8];
};
typedef char AODHordeContain_size[(sizeof(AODHordeContain) == 0x8E0) ? 1 : -1];
typedef char AODHordeContain_off_m_unk0x318[(offsetof(AODHordeContain, m_unk0x318) == 0x318) ? 1 : -1];
typedef char AODHordeContain_off_m_unk0x31C[(offsetof(AODHordeContain, m_unk0x31C) == 0x31C) ? 1 : -1];
typedef char AODHordeContain_off_m_unk0x320[(offsetof(AODHordeContain, m_unk0x320) == 0x320) ? 1 : -1];
typedef char AODHordeContain_off_m_unk0x334[(offsetof(AODHordeContain, m_unk0x334) == 0x334) ? 1 : -1];

#endif
