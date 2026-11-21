// NetPacket.h: the network packet class (Zero Hour's NetPacket by role; offsets are retail's).
// Target facts (code RVAs, VA 0x00C70A28 table):
//  - SIZE 0x204 (0x201 bytes of members, padded). One slot: the destructor 0x0058D0E2. The members: the packet bytes
//    at +4 (0x1DC of them, the most a datagram carries), the length +0x1E0, the sender's address +0x1E4 (an
//    ip dword and a port word, copied as two dwords), the command count +0x1EC (init writes 0, the constructor from a
//    received message -1), the last command added +0x1F0 (a NetCommandRef the destructor and reset release with
//    detach and operator delete), and the "last written" state that lets consecutive commands omit repeated fields:
//    execution frame +0x1F4, time stamp +0x1F8, command id word +0x1FC, player byte +0x1FE, command type byte +0x1FF and
//    relay byte +0x200 (isRoomForFrameMessage 0x0058D686 charges each field that differs from the message being added:
//    type 2, relay 2, player 2 and a forced id 3, time stamp 5, frame 5, plus 9, against the 0x1DC limit).
//  - Constructors: 0x0058E5B4 runs init; 0x0058E5EC (from a TransportMessage) runs init, copies the address, the length and
//    0x1DC bytes of data, and sets the count to -1. init 0x0058D10A clears everything; reset 0x0058D160 releases the last
//    command and runs init.
#pragma once
#ifndef BFME2_NETPACKET_H
#define BFME2_NETPACKET_H

#include "Common/GameMessageArgument.h"
#include "Common/GameType.h"
#include "GameNetwork/NetPacketAddress.h"

class NetCommandList;
class NetCommandRef;
namespace _STL { template <class T> class allocator; template <class T, class A> class list; }	// the list is only returned by value (defined where <list> is included)

class NetCommandRef;
class NetCommandMsg;
class GameMessage;
struct TransportMessage;

class NetPacket
{
	friend class Connection;	// Connection::doSend 0x0058BB5C reads the buffer, length, count and address of a packet it queues
public:
	NetPacket();												// 0x0058E5B4
	NetPacket(TransportMessage *message);						// 0x0058E5EC
	virtual ~NetPacket();										// slot 0, 0x0058D0E2

	NetCommandList *getCommandList();
	Bool addCommand(NetCommandRef *msg);
	static _STL::list<NetPacket *, _STL::allocator<NetPacket *> > ConstructBigCommandPacketList(NetCommandRef *msg);	// 0x005946E1 (splits a command that does not fit one packet into wrapper packets)
	const NetPacketAddress &getAddress() const { return m_addr; }	// inline: ConnectionManager::doRelay 0x004D3221 copies the two fields
	void init();
	Int rva0058E57B();											// (a count of eight-byte groups in the packet: len / 8 rounded up; the map has no better name)
	void reset();

	Bool rva0058D18C(NetCommandRef *msg);
	Bool rva0058D296(NetCommandRef *msg);						// (the hero message: adds its data length)
	Bool rva0058D211(NetCommandRef *msg);
	Bool rva0058D310(NetCommandRef *msg);
	Bool rva0058D58A(NetCommandRef *msg);
	Bool rva0058D601(NetCommandRef *msg);

	static NetCommandMsg *readAckBothMessage(UnsignedByte *data, Int &offset);
	static NetCommandMsg *readAckStage1Message(UnsignedByte *data, Int &offset);
	static NetCommandMsg *readAckStage2Message(UnsignedByte *data, Int &offset);
	static NetCommandMsg *readFrameMessage(UnsignedByte *data, Int &offset);
	static NetCommandMsg *readKeepAliveMessage(UnsignedByte *data, Int &offset);
	static NetCommandMsg *readDisconnectKeepAliveMessage(UnsignedByte *data, Int &offset);
	static NetCommandMsg *readDisconnectPlayerMessage(UnsignedByte *data, Int &offset);

	static NetCommandMsg *readRouterFallbackMessage(UnsignedByte *data, Int &offset);
	static NetCommandMsg *readPlayerLeaveMessage(UnsignedByte *data, Int &offset);
	static NetCommandMsg *readDestroyPlayerMessage(UnsignedByte *data, Int &offset);
	static NetCommandMsg *readDisconnectVoteMessage(UnsignedByte *data, Int &offset);
	static NetCommandMsg *readProgressMessage(UnsignedByte *data, Int &offset);
	static NetCommandMsg *rva0058E20D(UnsignedByte *data, Int &offset);	// (the hero message reader)
	static NetCommandMsg *rva0058E2D7(UnsignedByte *data, Int &offset);	// (the file progress reader)
	static NetCommandMsg *readInformPlayerLeaveFrameMessage(UnsignedByte *data, Int &offset);
	static NetCommandMsg *readGameMessage(UnsignedByte *data, Int &offset);
	static NetCommandMsg *readLoadCompleteMessage(UnsignedByte *data, Int &offset);	// 0x0058E0B0 (type 16; folded with the type 17 reader below: one body, no row of its own)
	static NetCommandMsg *readCommandType17Message(UnsignedByte *data, Int &offset);	// 0x0058E0B0 (type 17)
	static NetCommandMsg *readGameSpyStatsAuthKeyMessage(UnsignedByte *data, Int &offset);	// 0x00592520 (type 6; the map holds it as the free function Rva00592520Read)
	static NetCommandMsg *rva00592208(UnsignedByte *data, Int &offset);	// (type 30, the wide-string message; the map has no better name)
	static NetCommandMsg *readFileMessage(UnsignedByte *data, Int &offset);	// 0x005922FB (type 19: the map holds it as the free function Rva005922FBRead; getCommandList case 19)
	static NetCommandMsg *readFileAnnounceMessage(UnsignedByte *data, Int &offset);	// 0x005923C5 (type 21: the map holds it as Rva005923C5Read)
	static NetCommandMsg *readRequestGameSpyStatsAuthKeyMessage(UnsignedByte *data, Int &offset);	// 0x00592496 (type 5: the map holds it as Rva00592496Read)
	static NetCommandMsg *readRequestPlayerLeaveMessage(UnsignedByte *data, Int &offset);
	static NetCommandMsg *readRequestFrameDataMessage(UnsignedByte *data, Int &offset);
	static NetCommandMsg *readDisconnectFrameMessage(UnsignedByte *data, Int &offset);
	static NetCommandMsg *readChatMessage(UnsignedByte *data, Int &offset);
	static NetCommandMsg *readDisconnectChatMessage(UnsignedByte *data, Int &offset);
	UnsignedByte rva0059192A(NetCommandRef *msg);				// (room for a disconnect chat line)
	UnsignedByte rva005919AF(NetCommandRef *msg);				// (room for a chat line)
	UnsignedByte rva0059188C(NetCommandRef *msg);				// (room for a file announcement)
	UnsignedByte rva00591D0D(NetCommandRef *msg);				// (room for a stats key request)

	static NetCommandRef *ConstructNetCommandMsgFromRawData(UnsignedByte *data, UnsignedShort dataLength);

protected:
	static UnsignedInt GetBufferSizeNeededForCommand(NetCommandMsg *msg);
	static UnsignedInt GetGameCommandSize(NetCommandMsg *msg);
	static void FillBufferWithGameCommand(UnsignedByte *buffer, NetCommandRef *ref);
	static void FillBufferWithProgressMessage(UnsignedByte *buffer, NetCommandRef *ref);
	static void FillBufferWithAckCommand(UnsignedByte *buffer, NetCommandRef *ref);
	static void FillBufferWithRouterFallbackCommand(UnsignedByte *buffer, NetCommandRef *ref);
	static void FillBufferWithKeepAliveCommand(UnsignedByte *buffer, NetCommandRef *ref);	// 0x0058CACA (type 12)
	static void rva0058CACAType25(UnsignedByte *buffer, NetCommandRef *ref);	// folded into 0x0058CACA (type 25, the disconnect keep-alive)
	static void rva0058CCF2Type17(UnsignedByte *buffer, NetCommandRef *ref);	// folded into 0x0058CCF2 (type 17)
	static void rva0058CF83Type9(UnsignedByte *buffer, NetCommandRef *ref);	// folded into 0x0058CF83 (type 9, the frame-data request)
	static void FillBufferWithCommand(UnsignedByte *buffer, NetCommandRef *ref);
	static void rva0059129F(UnsignedByte *buffer, NetCommandRef *ref);	// (type 30, the wide-string message; the map has no better name)
	static void FillBufferWithChatCommand(UnsignedByte *buffer, NetCommandRef *ref);
	static void FillBufferWithFileCommand(UnsignedByte *buffer, NetCommandRef *ref);
	static void FillBufferWithFileAnnounceCommand(UnsignedByte *buffer, NetCommandRef *ref);
	static void FillBufferWithRequestGameSpyStatsAuthKeyCommand(UnsignedByte *buffer, NetCommandRef *ref);
	static void FillBufferWithGameSpyStatsAuthKeyCommand(UnsignedByte *buffer, NetCommandRef *ref);
	static NetCommandMsg *readWrapperMessage(UnsignedByte *data, Int &offset);
	Bool addDisconnectFrameCommand(NetCommandRef *msg);
	Bool addWrapperCommand(NetCommandRef *msg);
	Bool addFileCommand(NetCommandRef *msg);
	Bool addFileAnnounceCommand(NetCommandRef *msg);
	Bool addRequestGameSpyStatsAuthKeyCommand(NetCommandRef *msg);
	Bool addGameSpyStatsAuthKeyCommand(NetCommandRef *msg);
	Bool isRoomForFileMessage(NetCommandRef *msg);
	Bool isRoomForGameSpyStatsAuthKeyMessage(NetCommandRef *msg);
	Bool addChatCommand(NetCommandRef *msg);
	Bool addDisconnectChatCommand(NetCommandRef *msg);
	Bool addInformPlayerLeaveFrameCommand(NetCommandRef *msg);
	Bool addDestroyPlayerCommand(NetCommandRef *msg);
	Bool addDisconnectPlayerCommand(NetCommandRef *msg);
	Bool addDisconnectVoteCommand(NetCommandRef *msg);
	Bool addPlayerLeaveCommand(NetCommandRef *msg);
	Bool addFileProgressCommand(NetCommandRef *msg);
	Bool addProgressMessage(NetCommandRef *msg);
	Bool addFrameCommand(NetCommandRef *msg);
	Bool addRouterFallbackCommand(NetCommandRef *msg);
	Bool addGameCommand(NetCommandRef *msg);
	// Adders the linker folded into one body each (addCommand calls them from separate case blocks, so they are separate
	// functions in the source): the three ack types 0x005939EE, the two keep-alive types 0x0058FE15, the load-complete and
	// type 17 messages 0x0058F5E3, and the player-leave and frame-data requests 0x0058E8EA.
	Bool addAckBothCommand(NetCommandRef *msg);					// 0x005939EE
	Bool addAckStage1Command(NetCommandRef *msg);				// 0x005939EE
	Bool addAckStage2Command(NetCommandRef *msg);				// 0x005939EE
	Bool addKeepAliveCommand(NetCommandRef *msg);				// 0x0058FE15
	Bool addDisconnectKeepAliveCommand(NetCommandRef *msg);		// 0x0058FE15
	Bool addLoadCompleteCommand(NetCommandRef *msg);			// 0x0058F5E3
	Bool addCommandType17(NetCommandRef *msg);					// 0x0058F5E3
	Bool addRequestPlayerLeaveCommand(NetCommandRef *msg);		// 0x0058E8EA
	Bool addRequestFrameDataCommand(NetCommandRef *msg);		// 0x0058E8EA
	Bool rva0058EDEF(NetCommandRef *msg);
	UnsignedByte rva00591A65(NetCommandRef *msg);
	Bool rva005936DB(NetCommandRef *msg);
	Bool isRoomForFrameMessage(NetCommandRef *msg);
	Bool isAckBothRepeat(NetCommandRef *msg);
	Bool isAckStage1Repeat(NetCommandRef *msg);
	Bool isAckStage2Repeat(NetCommandRef *msg);					// folded into 0x0058D7B6
	Bool isAckRepeat(NetCommandRef *msg);
	Bool addAckCommand(NetCommandRef *msg, UnsignedShort commandID, UnsignedByte originalPlayerID, UnsignedInt originalTimestamp, UnsignedInt originalFrame);	// (the shared writer behind the three ack arms)
	void writeGameMessageArgumentToPacket(GameMessageArgumentDataType type, GameMessageArgumentType arg);
	Bool isRoomForWrapperMessage(NetCommandRef *msg);
	Bool isRoomForGameMessage(NetCommandRef *msg, GameMessage *gameMessage);
	UnsignedByte rva0058D70B(NetCommandRef *msg);
	Bool rva0058D408(NetCommandRef *msg);
	Bool rva0058D461(NetCommandRef *msg);
	Bool rva0058D4BA(NetCommandRef *msg);
	UnsignedByte rva0058D513(NetCommandRef *msg);


	UnsignedByte m_packet[0x1DC];								// +0x004
	Int m_packetLen;											// +0x1E0
	NetPacketAddress m_addr;									// +0x1E4
	Int m_numCommands;											// +0x1EC
	NetCommandRef *m_lastCommand;								// +0x1F0
	UnsignedInt m_lastFrame;									// +0x1F4
	UnsignedInt m_lastTimestamp;								// +0x1F8
	UnsignedShort m_lastCommandID;								// +0x1FC
	UnsignedByte m_lastPlayerID;								// +0x1FE
	UnsignedByte m_lastCommandType;								// +0x1FF
	UnsignedByte m_lastRelay;									// +0x200
	unsigned char m_pad201[3];									// +0x201
};
// SIZE 0x204
typedef char NetPacketSize[(sizeof(NetPacket) == 0x204) ? 1 : -1];

#endif
