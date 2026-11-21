// NetSaveGameCommandMsg.h: multiplayer save-game network command (command type 30, BFME II only).
// Target facts (retail game.dat): SIZE 0x28: NetCommandMsg (0x1C), action +0x1C, reason +0x20,
// filename UnicodeString +0x24. The file carries the role name while the class name Rva004D67D0
// is forced by the ledger's existing keys until renamed.
#pragma once
#ifndef BFME2_NETSAVEGAMECOMMANDMSG_H
#define BFME2_NETSAVEGAMECOMMANDMSG_H

#include "GameNetwork/NetCommandMsg.h"
#include "Common/UnicodeString.h"

class Rva004D67D0 : public NetCommandMsg
{
public:
	Rva004D67D0();
protected:
	virtual ~Rva004D67D0();									// slot 0
public:
	virtual AsciiString getContentsAsAsciiString();			// slot 3

	UnicodeString getFilename() const;
	void setFilename(UnicodeString filename);
	Int getAction() const { return m_action; }
	Int getReason() const { return m_reason; }
	void setAction(Int action) { m_action = action; }
	void setReason(Int reason) { m_reason = reason; }

	Int m_action;											// +0x1C
	Int m_reason;											// +0x20
	UnicodeString m_filename;								// +0x24
};
// SIZE 0x28
typedef char Rva004D67D0Size[(sizeof(Rva004D67D0) == 0x28) ? 1 : -1];

#endif
