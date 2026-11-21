// NetSaveGameCommandMsg.h: multiplayer save-game network command (command type 30, BFME II only;
// replaces Draft/Rva004D67D0.h). The map names the class Rva004D67D0 (constructor 0x004D674D,
// destructor 0x004D67D0, deleting 0x004D67B4, getContentsAsAsciiString 0x004D6806; vtable
// VA 0x00860560).
// Target facts (code RVAs): SIZE 0x28: NetCommandMsg (0x1C), action +0x1C, reason +0x20,
// filename UnicodeString +0x24. NetPacket::rva00592208 (0x00592208) constructs it and fills
// filename through 0x004D05D7; NetPacket::rva0059129F / rva00591A65 / rva005936DB / Rva00590FA5Get
// read filename through 0x0023E928.
#pragma once
#ifndef BFME2_NETSAVEDGAMECOMMANDMSG_H
#define BFME2_NETSAVEDGAMECOMMANDMSG_H

#include "GameNetwork/NetCommandMsg.h"
#include "Common/UnicodeString.h"

class Rva004D67D0 : public NetCommandMsg
{
public:
	Rva004D67D0();												// 0x004D674D
protected:
	virtual ~Rva004D67D0();										// slot 0, 0x004D67D0 (deleting 0x004D67B4)
public:
	virtual AsciiString getContentsAsAsciiString();				// slot 3, 0x004D6806

	UnicodeString getFilename() const;							// 0x0023E928
	void setFilename(UnicodeString filename);					// 0x004D05D7
	Int getAction() const { return m_action; }
	Int getReason() const { return m_reason; }
	void setAction(Int action) { m_action = action; }
	void setReason(Int reason) { m_reason = reason; }

	Int m_action;												// +0x1C
	Int m_reason;												// +0x20
	UnicodeString m_filename;									// +0x24
};
// SIZE 0x28
typedef char Rva004D67D0Size[(sizeof(Rva004D67D0) == 0x28) ? 1 : -1];

#endif
