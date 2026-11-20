// FrameDataManager.h: a ring of FrameData, one per frame (Zero Hour's FrameDataManager by role; offsets are retail's).
// Target facts (code RVAs, VA 0x00C70A0C table):
//  - SIZE 0x10. The constructor 0x0058B567 stores the table, the argument byte +8, allocates FRAME_DATA_LENGTH
//    FrameData (0x14 bytes each, with the usual four-byte count in front) and clears +0xC and +9. The only slot is the
//    scalar deleting destructor 0x0058B86E; the destructor 0x0058B623 re-stores the table, inits every frame and frees the
//    array. +9 is the quitting flag set by setQuitFrame 0x0058B818 (which stores the frame at +0xC).
//  - Every frame accessor takes a frame number and indexes the ring with frame % FRAME_DATA_LENGTH.
#pragma once
#ifndef BFME2_FRAMEDATAMANAGER_H
#define BFME2_FRAMEDATAMANAGER_H

#include "Common/GameType.h"
#include "GameNetwork/FrameData.h"
#include "GameNetwork/NetworkDefs.h"

class FrameDataManager
{
public:
	FrameDataManager(Bool isLocal);
	virtual ~FrameDataManager();							// slot 0, 0x0058B623 (deleting 0x0058B86E)

	void reset();
	NetCommandRef *addNetCommandMsg(NetCommandMsg *msg);
	FrameDataReturnType allCommandsReady(UnsignedInt frame, Bool debugSpewage);
	NetCommandList *getFrameCommandList(UnsignedInt frame);
	void resetFrame(UnsignedInt frame, Bool isAdvancing);
	UnsignedInt getCommandCount(UnsignedInt frame);
	void setFrameCommandCount(UnsignedInt frame, UnsignedInt count);
	UnsignedInt getFrameCommandCount(UnsignedInt frame);
	void zeroFrames(UnsignedInt startingFrame, UnsignedInt numFrames);
	void destroyGameMessages();
	void setQuitFrame(UnsignedInt frame);
	Bool getIsQuitting();
	UnsignedInt getQuitFrame() const;
	Int countCommandsOfType(UnsignedInt frame, Int type);	// (the frame's ring entry counts the messages of that command type)
	UnsignedInt getAckCommandCount(UnsignedInt frame);

	FrameData *m_frameData;									// +0x04
	Bool m_isLocal;											// +0x08
	Bool m_isQuitting;										// +0x09
	unsigned char m_pad0A[2];								// +0x0A
	UnsignedInt m_quitFrame;								// +0x0C
};
// SIZE 0x10
typedef char FrameDataManagerSize[(sizeof(FrameDataManager) == 0x10) ? 1 : -1];

#endif
