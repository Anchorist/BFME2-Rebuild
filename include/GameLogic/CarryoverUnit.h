#pragma once

#include "Common/AsciiString.h"
#include "Common/GameType.h"
#include "Common/Snapshot.h"
#include "Common/UnicodeString.h"
#include "Common/UpgradeMaskType.h"

// Constructor 0x0037DF2C and destructor 0x0037DEE4 install the four-slot
// Snapshot table 0x007DF158. ArmySummaryEntry starts its other base at +0xAC.
class CarryoverUnit : public Snapshot
{
public:
	CarryoverUnit();	// 0x0037DF2C
	virtual ~CarryoverUnit();	// 0x0037DEE4

protected:
	virtual void loadPostProcess() {}	// empty 0x000B3FD0
	virtual const char *GetSnapshotName() const;	// 0x0037DC84
	virtual void xfer(Xfer *xfer);	// 0x0037DE79

private:
	// 0x004E0513 transfers three Int values, the wide and narrow strings,
	// then a Bool introduced in version 4.
	struct UnitState
	{
		Int m_unk0x00;
		Int m_unk0x04;
		Int m_unk0x08;
		UnicodeString m_unk0x0C;
		AsciiString m_unk0x10;
		Bool m_unk0x14;
	};

	AsciiString m_unitTemplateName;	// +0x04, compared in 0x0037E10C and passed to the template lookup path at 0x0037DF8D
	Real m_unk0x08;	// Xfer Real at 0x0037DEB8
	Int m_unk0x0C;	// Xfer Int at 0x0037DEDB
	UpgradeMaskType m_upgrades;	// +0x10, initialized at 0x0037DF67 and transferred at 0x0037DECC
	Int m_unk0x90;	// Xfer Int at 0x0037DEAD
	UnitState m_unitState;	// +0x94, ctor 0x004E04FD and xfer 0x004E0513
};

typedef char CarryoverUnit_size[(sizeof(CarryoverUnit) == 0xAC) ? 1 : -1];
