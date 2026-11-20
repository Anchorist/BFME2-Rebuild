// NetCommandWrapperList.h: the wrapped commands being reassembled (Zero Hour's NetCommandWrapperList;
// names are theirs by role, offsets are retail's).
// Target facts (code RVAs, VA 0x00C70A24 table): SIZE 8. The constructor 0x0058C0AE clears the list head
// +4 and stores the table of one slot, the scalar deleting destructor 0x0058C268 (destructor 0x0058C0BB,
// protected). reset 0x0058C0F0 and the destructor free every node through its virtual destructor (flag 0) and
// the global operator delete.
#pragma once
#ifndef BFME2_NETCOMMANDWRAPPERLIST_H
#define BFME2_NETCOMMANDWRAPPERLIST_H

#include "Common/GameType.h"

class NetCommandList;
class NetCommandRef;
class NetCommandWrapperListNode;

class NetCommandWrapperList
{
public:
	NetCommandWrapperList();

	friend class ConnectionManager;						// ~ConnectionManager 0x004D2344 deletes the list through the virtual destructor
protected:
	virtual ~NetCommandWrapperList();						// slot 0, 0x0058C0BB (deleting 0x0058C268)

public:
	void init();											// (folded dword clearer: m_list = 0)
	void reset();
	void processWrapper(NetCommandRef *ref);
	NetCommandList *getReadyCommands();
	Int getPercentComplete(UnsignedShort wrappedCommandID);

protected:
	void removeFromList(NetCommandWrapperListNode *node);

	NetCommandWrapperListNode *m_list;						// +0x04
};
// SIZE 0x08

#endif
