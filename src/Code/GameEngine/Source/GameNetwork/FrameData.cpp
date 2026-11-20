// cl: /O1
#include "GameNetwork/FrameData.h"
#include "GameNetwork/NetCommandList.h"
#include "GameNetwork/NetCommandMsg.h"





// Reference object O005DA4C8.
// FUNCTION: BFME2 0x005DA4C8 size=20 name=??0FrameData@@QAE@XZ evidence=N:ledger tier=B hypothesis:name:Z
FrameData::FrameData()
{
	m_frameCommandCount = -1;
	m_commandList = 0;
	m_commandCount = 0;
	m_lastFailedCC = 0;
	m_lastFailedFrameCC = 0;
}

// FUNCTION: BFME2 0x005DA4DC size=29 name=??1FrameData@@QAE@XZ evidence=N:ledger tier=B hypothesis:Z
FrameData::~FrameData()
{
	if (m_commandList != 0)
	{
		::delete m_commandList;
		m_commandList = 0;
	}
}

// FUNCTION: BFME2 0x005DA4F9 size=101 name=?init@FrameData@@QAEXXZ evidence=N:ledger tier=B hypothesis:Z
void FrameData::init()
{
	if (m_commandList == 0)
	{
		m_commandList = new NetCommandList();
		m_commandList->reset();
	}
	m_commandList->reset();
	m_frameCommandCount = -1;
	m_commandCount = 0;
	m_lastFailedCC = -2;
	m_lastFailedFrameCC = -2;
}

// FUNCTION: BFME2 0x005DA563 size=75 name=?allCommandsReady@FrameData@@QAE?AW4FrameDataReturnType@@_N@Z evidence=N:ledger tier=B hypothesis:Z
FrameDataReturnType FrameData::allCommandsReady(Bool debugSpewage)
{
	if (m_frameCommandCount == m_commandCount)
	{
		m_lastFailedFrameCC = -2;
		m_lastFailedCC = -2;
		return FRAMEDATA_READY;
	}
	if (debugSpewage)
	{
		if (m_lastFailedFrameCC != m_frameCommandCount || m_lastFailedCC != m_commandCount)
		{
			m_lastFailedFrameCC = m_frameCommandCount;
			m_lastFailedCC = m_commandCount;
		}
	}
	// More commands arrived than the frame announced: drop them all and ask for the frame again.
	if (m_commandCount > m_frameCommandCount)
	{
		// The reference follows the whole chain here before resetting the frame.
		NetCommandRef *ref = m_commandList->m_first;
		while (ref != 0)
			ref = ref->m_next;
		init();
		return FRAMEDATA_RESEND;
	}
	return FRAMEDATA_NOTREADY;
}

// FUNCTION: BFME2 0x005DA5AE size=53 name=?addCommand@FrameData@@QAEPAVNetCommandRef@@PAVNetCommandMsg@@@Z evidence=N:ledger tier=B hypothesis:Z
NetCommandRef *FrameData::addCommand(NetCommandMsg *msg)
{
	if (m_commandList == 0)
		init();
	if (m_commandList->findMessage(msg) != 0)
		return 0;
	NetCommandRef *ref = m_commandList->addMessage(msg);
	++m_commandCount;
	return ref;
}

// FUNCTION: BFME2 0x005DA5E3 size=8 name=?zeroFrame@FrameData@@QAEXXZ evidence=N:ledger tier=B hypothesis:Z
void FrameData::zeroFrame()
{
	m_commandCount = 0;
	m_frameCommandCount = 0;
}

// FUNCTION: BFME2 0x005DA5EB size=21 name=?destroyGameMessages@FrameData@@QAEXXZ evidence=N:ledger tier=B hypothesis:Z
void FrameData::destroyGameMessages()
{
	if (m_commandList != 0)
	{
		m_commandList->reset();
		m_commandCount = 0;
	}
}

// FUNCTION: BFME2 0x005DA600 size=33 name=?countCommandsOfType@FrameData@@QBEHH@Z evidence=X:map request tier=B hypothesis:Z
Int FrameData::countCommandsOfType(Int type) const
{
	Int count = 0;
	if (m_commandList != 0)
	{
		for (NetCommandRef *ref = m_commandList->m_first; ref != 0; ref = ref->m_next)
		{
			if (ref->m_command->getNetCommandType() == type)
				++count;
		}
	}
	return count;
}

// FUNCTION: BFME2 0x005DA621 size=42 name=?getAckCommandCount@FrameData@@QAEIXZ evidence=N:ledger tier=B hypothesis:Z
UnsignedInt FrameData::getAckCommandCount()
{
	if (m_commandList == 0)
		return 0;
	UnsignedInt count = 0;
	for (NetCommandRef *ref = m_commandList->m_first; ref != 0; ref = ref->m_next)
	{
		if (CommandRequiresAck(ref->m_command))
			++count;
	}
	return count;
}


// The reference reset entry (0x005DA55E) jumps directly to init.
void FrameData::reset()
{
	init();
}
