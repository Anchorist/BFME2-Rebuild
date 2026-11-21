// BuddyDefs.h: small record types defined in BuddyDefs.cpp (ledger-named structs; member names
// are offset placeholders for roles not yet proven).
// Target facts (code RVAs):
//  - BfmeStringRecord00415F34 (SIZE 0x18): default ctor 0x00415F26 zeroes +0x08, +0x10, +0x14
//    only (AsciiString, AsciiString, UnicodeString); copy ctor 0x00415F34 copies +0x00, +0x04,
//    +0x08, +0x0C, +0x10, +0x14 in order.
//  - Rva004160BEInfo (SIZE 0x18): method rva004160BE 0x004160BE reads +0x04, +0x08, +0x14 (Int)
//    and +0x0C, +0x10 (AsciiString).
#pragma once
#ifndef BFME2_BUDDYDEFS_H
#define BFME2_BUDDYDEFS_H

#include <stddef.h>
#include "Common/GameType.h"
#include "Common/AsciiString.h"
#include "Common/UnicodeString.h"

struct BfmeStringRecord00415F34
{
	Int m_unk0x00;										// +0x00
	Int m_unk0x04;										// +0x04
	AsciiString m_unk0x08;								// +0x08
	Int m_unk0x0C;										// +0x0C
	AsciiString m_unk0x10;								// +0x10
	UnicodeString m_unk0x14;							// +0x14

	BfmeStringRecord00415F34();							// 0x00415F26
	BfmeStringRecord00415F34(const BfmeStringRecord00415F34 &other);	// 0x00415F34
};
// SIZE 0x18
typedef char BfmeStringRecord00415F34_size[(sizeof(BfmeStringRecord00415F34) == 0x18) ? 1 : -1];
typedef char BfmeStringRecord00415F34_off_m_unk0x08[(offsetof(BfmeStringRecord00415F34, m_unk0x08) == 0x08) ? 1 : -1];
typedef char BfmeStringRecord00415F34_off_m_unk0x10[(offsetof(BfmeStringRecord00415F34, m_unk0x10) == 0x10) ? 1 : -1];
typedef char BfmeStringRecord00415F34_off_m_unk0x14[(offsetof(BfmeStringRecord00415F34, m_unk0x14) == 0x14) ? 1 : -1];

struct Rva004160BEInfo
{
	Int m_unk0x00;										// +0x00
	Int m_unk0x04;										// +0x04
	Int m_unk0x08;										// +0x08
	AsciiString m_unk0x0C;								// +0x0C
	AsciiString m_unk0x10;								// +0x10
	Int m_unk0x14;										// +0x14

	// 0x004160BE: formats "%d %d %d PW:%s #HOST:%s" from +0x04, +0x08, +0x14, +0x10, +0x0C.
	AsciiString rva004160BE() const;
};
// SIZE 0x18
typedef char Rva004160BEInfo_size[(sizeof(Rva004160BEInfo) == 0x18) ? 1 : -1];
typedef char Rva004160BEInfo_off_m_unk0x0C[(offsetof(Rva004160BEInfo, m_unk0x0C) == 0x0C) ? 1 : -1];
typedef char Rva004160BEInfo_off_m_unk0x10[(offsetof(Rva004160BEInfo, m_unk0x10) == 0x10) ? 1 : -1];
typedef char Rva004160BEInfo_off_m_unk0x14[(offsetof(Rva004160BEInfo, m_unk0x14) == 0x14) ? 1 : -1];

#endif
