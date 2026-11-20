// ScriptEngine state for a running script sequence. Native constructor
// 0x0020479E installs table 0x007E3A90, and destructor 0x00205224
// restores the Snapshot table. ScriptActions allocates 0x2C at 0x003C0AC0.
#pragma once

#include "Common/AsciiString.h"
#include "Common/GameType.h"
#include "Common/Snapshot.h"

class Script;
class Team;

class SequentialScript : public Snapshot
{
public:
	SequentialScript();
	virtual ~SequentialScript();						// 0x00205224
	virtual void loadPostProcess() {}					// slot 1: native 0x000B3FD0 is a bare return
	virtual const char *GetSnapshotName() const;				// slot 2: 0x002047C9 returns "SequentialScript"

protected:
	virtual void xfer(Xfer *xfer);						// slot 3: 0x002039D4

public:
	Team *m_teamToExecOn;							// +0x04, setSequentialTimer 0x00204002
	ObjectID m_objectID;							// +0x08, setSequentialTimer 0x00203FCF
	AsciiString m_scriptScope;						// +0x0C, xfer 0x002039D4 passes it as the lookup scope
	AsciiString m_scriptName;						// +0x10, xfer passes it as the name and 0x003C0A6B stores it
	Script *m_script;							// +0x14, xfer stores findScriptInScope's Script *
	Int m_currentInstruction;						// +0x18, constructor sets -1
	Int m_timesToLoop;							// +0x1C, ScriptActions 0x003C0B44
	Int m_framesToWait;							// +0x20, both setSequentialTimer overloads
	Bool m_dontAdvanceInstruction;						// +0x24, transferred by xfer
	SequentialScript *m_nextScriptInSequence;				// +0x28
};

typedef char SequentialScriptSizeCheck[sizeof(SequentialScript) == 0x2C ? 1 : -1];
