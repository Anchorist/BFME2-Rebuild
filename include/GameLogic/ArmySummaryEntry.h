#pragma once

#include "Apt/AptRef.h"
#include "GameLogic/CarryoverUnit.h"

// 0x0040C351 builds CarryoverUnit at +0 and AptRefTarget at +0xAC.
// The secondary deleting thunk 0x0040C5D3 adjusts this by -0xAC.
// ArmySummary::xfer allocates 0xC8 bytes at 0x0040EFA5.
class ArmySummaryEntry : public CarryoverUnit, public AptRefTarget
{
public:
	ArmySummaryEntry();	// 0x0040C351
	virtual ~ArmySummaryEntry();	// 0x0040C39E

protected:
	virtual const char *GetSnapshotName() const;	// 0x0040C586
	virtual void xfer(Xfer *xfer);	// 0x0040C4FE

private:
	Int m_buildingID;	// +0xB4, XferLivingWorldBuildingID via 0x0040C53D
	Int m_livingWorldArmyID;	// +0xB8, XferLivingWorldArmyID via 0x0040C54A
	Int m_upgradeBuildingID;	// +0xBC, set and cleared by MarkForUpgrades and CancelUpgrades
	UnsignedByte m_unk0xC0[4];	// compared as one word at 0x0040C40E
	Bool m_unk0xC4;	// Xfer Bool at 0x0040C55D
	Bool m_unk0xC5;	// Xfer Bool at 0x0040C52F
};

typedef char ArmySummaryEntry_size[(sizeof(ArmySummaryEntry) == 0xC8) ? 1 : -1];
