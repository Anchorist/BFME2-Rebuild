// ConnectionManager.h: the per-game network session object (Zero Hour's ConnectionManager by role: the
// eight Connections, the Transport, the frame data and the command lists; names are theirs where a retail
// body agrees, offsets are retail's).
// Target facts (code RVAs, VA 0x00C601C0 table):
//  - SIZE 0x121B0 (the allocation at 0x0025DF01 passes 0x121B0). Constructor 0x004D274B stores the table at
//    +0 (no base constructor), builds nine 0x2000-byte CommandIDHistory objects at +0x24 with the vector
//    constructor iterator over 0x004D13EA, and initialises the members below; the destructor 0x004D2344 is
//    not virtual and stores the same table first.
//  - Table (4 slots): 0 init 0x004D24A2, 1 reset 0x004D0669, 2 0x004CF032 (releases the frame data and
//    clears the per-slot arrays; the map calls it BFMEConnectionManager::init, which is not a retail name),
//    3 update(bool, int) 0x004D342A.
//  - +4: eight Connection pointers (indexed by player slot). +0x24: nine CommandIDHistory (one per slot and
//    one extra at +0x10024 that 0x004D2667 uses for the local player's own commands). +0x12024 Transport
//    (attachTransport 0x004CF113 destroys the old one first), +0x12028 local slot, +0x1202C packet router
//    slot (getLocalPlayerID 0x004CF906 / getPacketRouterSlot 0x004CF3B2), +0x12030 eight fallback router
//    slots (-1), +0x12050 dword and +0x12054 word (an address, zeroed), +0x12058 the local player's name
//    (getPlayerName 0x004D0198 returns it for the local slot, the Connection's name for another slot, or the
//    empty string).
//  - Per-slot arrays: +0x12060 (IsFrameAcked 0x004CF316 compares each connected slot's value with the frame;
//    sendFrameDataToPlayer 0x004D04A4 raises one with a max), +0x12080 (the slot state: isPlayerInGame
//    0x004CF0A6 tests == 1, isPlayerSlotActive 0x004CF0CD tests 1..3), +0x120A0 (1 after the constructor,
//    read by 0x004CF0FB which answers 1 for an out-of-range slot), +0x120C0 and +0x120E0 (zero).
//  - +0x12100 DisconnectManager (virtual destructor), +0x12104 eight FrameDataManager pointers, +0x12124 /
//    +0x12128 NetCommandLists (the destructor deletes each through its virtual destructor), +0x1212C the
//    NetCommandWrapperList, +0x12130 a time stamp (set by requestLeave 0x004D00BB when it is zero, cleared
//    by 0x004CF406, tested against ten seconds by 0x004CF3E1), +0x12134 / +0x12135 two bytes (0 and 1), then
//    twelve-byte STL containers at +0x12138, +0x12144 and eight at +0x12150, left as a typed gap until
//    their template identities are settled (their destructors are 0x004D21B4, 0x004D1AC3 and 0x004D0FAB).
#pragma once
#ifndef BFME2_CONNECTIONMANAGER_H
#define BFME2_CONNECTIONMANAGER_H

#include "Common/GameType.h"
#include "Common/UnicodeString.h"
#include "Common/AsciiString.h"
#include "GameNetwork/NetPacketAddress.h"
#include <map>
#include <bitset>

// What disconnectPlayer 0x004D13F8 answers (Zero Hour's PlayerLeaveCode by role). Values from retail: the body
// returns 3 for an out-of-range slot, stores 1 when the slot is the local one and 2 after it moved the packet router
// away from the leaving slot; processPlayerLeave 0x004D1D37 compares the answer with 2.
enum PlayerLeaveCode
{
	PLAYERLEAVECODE_CLIENT,
	PLAYERLEAVECODE_LOCALPLAYER,
	PLAYERLEAVECODE_PACKETROUTER,
	PLAYERLEAVECODE_NOLEAVE
};

class Connection;
class CreateAHeroData;
class Transport;
class DisconnectManager;
class FrameDataManager;
class NetCommandList;
class NetCommandMsg;
class NetCommandRef;
class NetCommandWrapperList;
class NetWrapperCommandMsg;
class NetProgressCommandMsg;
class NetFileProgressCommandMsg;
class NetFileCommandMsg;
class NetFileAnnounceCommandMsg;
class NetChatCommandMsg;
class NetDisconnectChatCommandMsg;
class GameMessage;
class GameInfo;
struct BfmeNetAddress;

// One bit per command id (0x10000 bits). Evidence: the constructor 0x004D13EA runs the bit-set constructor.
class CommandIDHistory
{
public:
	CommandIDHistory();										// 0x004D13EA
	void *rva004D04C9();									// (the map has no better name; disconnectPlayer calls it for the router's history)
	void rva004D1EB1(UnsignedShort commandID);				// (clears the twenty bits around the id ahead of a new one; accept calls it; the map has no better name)
	Int rva000D43D0();										// 0x000D43D0 (folded zero-returning stub called by Network::vslotF4)
	Bool accept(UnsignedShort commandID, UnsignedInt frame);	// 0x004D2164 (true when the id is new; false for a repeat)

	_STL::bitset<0x10000> m_bits;								// +0x0000
};
// SIZE 0x2000

// One entry of the list broadcastRouterFallbackPlan 0x004D0C88 sorts the connected players into (ascending score; 0xC bytes).
struct PlayerRouterScore
{
	Real score;
	Int player;
	PlayerRouterScore *next;
};

class ConnectionManager
{
public:
	ConnectionManager();									// 0x004D274B
	~ConnectionManager();									// Not virtual

	virtual void init();									// slot 0, 0x004D24A2
	virtual void reset();									// slot 1, 0x004D0669
	virtual void slot2();									// slot 2, 0x004CF032 (name not evidenced)
	virtual void update(Bool isInGame, Int frame);			// slot 3, 0x004D342A

	UnsignedInt getLocalPlayerID();
	UnsignedInt getPacketRouterSlot();
	Int getNumPlayers();
	UnsignedInt getNextPacketRouterSlot(UnsignedInt from);	// 0x004CFAC0 (the map calls it BFMEConnectionManager::getNextPacketRouterSlot)
	UnsignedInt rva004CFC81() const;						// (frames the slowest slot is behind; the map has no better name)
	void sendHero(CreateAHeroData *hero, Int slot, UnsignedShort commandID, UnsignedByte playerMask);
	void rva004D0E93(Int slot, Int frame, const UnicodeString &text);	// (the map has no better name)
	UnsignedByte rva004CEF58(Int slot);					// 0x004CEF58
	UnsignedByte isSlotWithinTimeout(Int slot, UnsignedInt timeout);	// 0x004CEFC2
	Int getSlotFrameLimit(Int slot);					// 0x004CF0FB
	Bool isPlayerConnected(Int slot);						// 0x004CF083 (the map calls it BFMEConnectionManager::isPlayerConnected)
	Bool isPlayerInGame(Int slot);							// 0x004CF0A6
	Bool isPlayerSlotActive(Int slot);						// 0x004CF0CD
	void attachTransport(Transport *transport);				// 0x004CF113
	Bool IsFrameAcked(UnsignedInt frame);
	Bool areAllQueuesEmpty();
	Bool rva004CF3E1();
	Bool isPacketRouter();									// 0x004CF9CD
	Bool areFrameCommandsComplete(UnsignedInt frame, Bool debugSpewage);	// 0x004CF799
	void setFrameGrouping(UnsignedInt grouping);
	void voteForPlayerDisconnect(Int slot);
	void resendPendingCommands();
	UnicodeString getPlayerName(Int slot);
	void disconnectLocalPlayer();
	PlayerLeaveCode disconnectPlayer(Int slot);
	PlayerLeaveCode processPlayerLeave(UnsignedByte playerID);
	void doRelay();
	void relayCommand(void *ref);							// 0x004CF578 (stamps a received command with the next frame and its time, stores it in the sender's frame data and forwards it to the relay targets; takes a NetCommandRef)
	void rva004D316A(NetCommandList *list, const BfmeNetAddress *from);	// (the map has no better name: handles every command of a received list)
	NetCommandList *getFrameCommandList(UnsignedInt frame);
	void parseUserList(const GameInfo *game);
	void initTransport();
	void sendChat(UnicodeString text, Int playerMask);
	void sendDisconnectChat(UnicodeString text);
	void sendFile(AsciiString path, UnsignedByte playerMask, UnsignedShort commandID);
	UnsignedShort sendFileAnnounce(AsciiString path, UnsignedByte playerMask);
	Int getFileTransferProgress(Int slot, AsciiString path);
	void resendFrameRangeToPlayer(Int slot, UnsignedInt firstFrame, UnsignedInt lastFrame);	// 0x004D0381 (the map calls it BFMEConnectionManager::resendFrameRangeToPlayer)
	void sendFrameDataToPlayer(UnsignedInt slot, UnsignedInt frame);
	void sendLocalCommand(NetCommandMsg *msg, UnsignedByte relay);
	void sendLocalCommandDirect(NetCommandMsg *msg, UnsignedByte relay);
	void loadProgressComplete();
	void quitGame();										// 0x004D0E8B (Zero Hour's name: asks to leave with reason 0; the map holds it as rva004D0E8B)
	void requestLeave(Int reason);
	void rva004CF8D5();										// 0x004CF8D5 (the map holds it as BfmeOwnerFY::bfmeShutdownFY)
	void updateLoadProgress(Int progress);
	void sendLocalGameMessage(GameMessage *msg);
	void processAck(NetCommandMsg *msg);					// 0x004D094C (the map calls it BFMEConnectionManager::processAck)
	void processAckCommand(void *msg);						// 0x004D0815 (the stage-2 half of an acknowledgement: retires the pending command and relays the final ack)
	void rva004CF35D(NetWrapperCommandMsg *msg);			// (the map has no better name)
	void processInformPlayerLeaveFrameCommand(void *msg);	// 0x004CFD06 (the map calls it BFMEConnectionManager::...)
	void processGameSpyStatsAuthKeyCommand(void *msg);		// 0x004CFE24
	void sendGameSpyStatsAuthKey(void *msg);				// 0x004D12B2
	void processRequestFrameDataCommand(void *msg);			// 0x004D0984
	void processHero(NetCommandMsg *msg);
	void sendKeepAliveCommand();							// 0x004CF828 (the map calls it BFMEConnectionManager::sendKeepAliveCommand)
	void sendDisconnectFrameCommand();						// 0x004CF9DF
	Bool hasPacketRouterFrameStall();						// 0x004CFBF9
	void SendFinishedLogicFrame();							// 0x004D0BE5
	void sendFrameInfo(Bool nextFrame);						// 0x004D0AA9
	Bool isDuplicateCommand(NetCommandMsg *msg);			// 0x004D2667
	void broadcastRouterFallbackPlan();						// 0x004D0C88 (orders the connected players by latency, penalising a client frame far behind the logic frame, and sends the plan to everybody)
	void sendPlayerLeaveCommand();							// 0x004D0A0A (broadcasts this player's leave command to everybody and stamps +0x12130; the map holds it under rva004D0A0A)

protected:
	void processAckStage1(NetCommandMsg *msg);				// 0x004CFCD1 (detaches and frees the acked command; the frame-latency metric Zero Hour updates here is not in retail)

private:
	void processProgress(NetProgressCommandMsg *msg);
	void processFileProgress(NetFileProgressCommandMsg *msg);
	Bool processNetCommand(NetCommandRef *ref);
	void ackCommand(NetCommandRef *ref, const BfmeNetAddress *from);	// (the acknowledgement for a received command)
	void processChat(NetChatCommandMsg *msg);
	void processDisconnectChat(NetDisconnectChatCommandMsg *msg);
	void processWrapper(NetCommandRef *ref);
	void processFile(NetFileCommandMsg *msg);
	void processFileAnnounce(NetFileAnnounceCommandMsg *msg);

public:

	Connection *m_connections[8];							// +0x004
	CommandIDHistory m_commandHistory[9];						// +0x024
	Transport *m_transport;									// +0x12024
	UnsignedInt m_localSlot;								// +0x12028
	UnsignedInt m_packetRouterSlot;							// +0x1202C
	Int m_packetRouterFallback[8];							// +0x12030 (-1)
	NetPacketAddress m_localAddress;						// +0x12050 (ip dword and port word, zeroed by the constructor; SetLocalAddr 0x0025DBDC fills it)
	UnicodeString m_localPlayerName;						// +0x12058
	UnsignedInt m_unk0x1205C;								// +0x1205C
	UnsignedInt m_ackedFrame[8];							// +0x12060
	Int m_slotState[8];										// +0x12080
	UnsignedInt m_unk0x120A0[8];							// +0x120A0 (1)
	UnsignedInt m_unk0x120C0[8];							// +0x120C0
	UnsignedInt m_unk0x120E0[8];							// +0x120E0
	DisconnectManager *m_disconnectManager;					// +0x12100
	FrameDataManager *m_frameData[8];						// +0x12104
	NetCommandList *m_pendingCommands;						// +0x12124
	NetCommandList *m_relayedCommands;						// +0x12128
	NetCommandWrapperList *m_wrapperList;					// +0x1212C
	UnsignedInt m_unk0x12130;								// +0x12130
	Bool m_unk0x12134;										// +0x12134
	Bool m_unk0x12135;										// +0x12135
	unsigned char m_pad12136[2];							// +0x12136
	_STL::map<UnsignedShort, AsciiString> m_fileNames;		// +0x12138 (file id -> path: processFileAnnounce 0x004D2C8E stores it, getFileTransferProgress 0x004D28C6 walks it comparing the path at node +0x14; destructor 0x004D21B4)
	_STL::map<UnsignedShort, UnsignedByte> m_filePlayerMasks;	// +0x12144 (file id -> player mask: processFileAnnounce stores the announce's mask byte; destructor 0x004D1AC3)
	_STL::map<UnsignedShort, Int> m_fileProgress[8];		// +0x12150 (one per player, file id -> percent: processFileProgress 0x004D2852 indexes this + (0x181C + player) * 12; the array destructor iterates 0x004D1D32)
};
// SIZE 0x121B0
typedef char ConnectionManagerSize[(sizeof(ConnectionManager) == 0x121B0) ? 1 : -1];

#endif
