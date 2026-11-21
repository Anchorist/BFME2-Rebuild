// cl: /O1
// psdk
// Portions derived from Command & Conquer Generals and Command & Conquer Generals Zero Hour, (c) Electronic Arts Inc., GPL-3.0-or-later; see LICENSE and NOTICE.
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G00581194 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include <ctype.h>
#include <winsock2.h>
#include "Common/AsciiString.h"
#include "GameNetwork/NetCommandMsg.h"

static UnsignedShort nextCommandID = 100;

static const Int kNetCommandTypeGameSpyStatsAuthKey = 6;
static const Int kNetCommandTypeTimeoutStart = 17;
static const Int kNetCommandTypeSaveGame = 30;

// FUNCTION: BFME2 0x00581194 size=20 name=?SeedNextCommandIDFromPlayerCount@@YAXG@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void SeedNextCommandIDFromPlayerCount(UnsignedShort playerCount)
{
	nextCommandID = (playerCount + 10) * 1000;
}

// FUNCTION: BFME2 0x005811A8 size=13 name=?GenerateNextCommandID@@YAGXZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
UnsignedShort GenerateNextCommandID()
{
	return nextCommandID++;
}

// FUNCTION: BFME2 0x005811B5 size=116 name=?DoesCommandRequireACommandID@@YA_NW4NetCommandType@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Bool DoesCommandRequireACommandID(NetCommandType type)
{
	return (type == NETCOMMANDTYPE_GAMECOMMAND ||
		type == NETCOMMANDTYPE_REQUESTGAMESPYSTATSAUTHKEY ||
		type == kNetCommandTypeGameSpyStatsAuthKey ||
		type == NETCOMMANDTYPE_FRAMEINFO ||
		type == NETCOMMANDTYPE_PLAYERLEAVE ||
		type == NETCOMMANDTYPE_INFORMPLAYERLEAVEFRAME ||
		type == NETCOMMANDTYPE_REQUESTFRAMEDATA ||
		type == NETCOMMANDTYPE_REQUESTPLAYERLEAVE ||
		type == NETCOMMANDTYPE_DESTROYPLAYER ||
		type == NETCOMMANDTYPE_CHAT ||
		type == NETCOMMANDTYPE_DISCONNECTVOTE ||
		type == NETCOMMANDTYPE_LOADCOMPLETE ||
		type == kNetCommandTypeTimeoutStart ||
		type == NETCOMMANDTYPE_WRAPPER ||
		type == NETCOMMANDTYPE_HERO ||
		type == NETCOMMANDTYPE_FILE ||
		type == NETCOMMANDTYPE_FILEANNOUNCE ||
		type == NETCOMMANDTYPE_FILEPROGRESS ||
		type == NETCOMMANDTYPE_DISCONNECTPLAYER ||
		type == NETCOMMANDTYPE_DISCONNECTFRAME ||
		type == kNetCommandTypeSaveGame);
}

// FUNCTION: BFME2 0x00581229 size=119 name=?CommandRequiresAck@@YA_NPAVNetCommandMsg@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Bool CommandRequiresAck(NetCommandMsg *msg)
{
	NetCommandType type = msg->getNetCommandType();
	return (type == NETCOMMANDTYPE_GAMECOMMAND ||
		type == NETCOMMANDTYPE_REQUESTGAMESPYSTATSAUTHKEY ||
		type == kNetCommandTypeGameSpyStatsAuthKey ||
		type == NETCOMMANDTYPE_FRAMEINFO ||
		type == NETCOMMANDTYPE_PLAYERLEAVE ||
		type == NETCOMMANDTYPE_INFORMPLAYERLEAVEFRAME ||
		type == NETCOMMANDTYPE_REQUESTFRAMEDATA ||
		type == NETCOMMANDTYPE_REQUESTPLAYERLEAVE ||
		type == NETCOMMANDTYPE_DESTROYPLAYER ||
		type == NETCOMMANDTYPE_CHAT ||
		type == NETCOMMANDTYPE_DISCONNECTVOTE ||
		type == NETCOMMANDTYPE_DISCONNECTPLAYER ||
		type == NETCOMMANDTYPE_LOADCOMPLETE ||
		type == kNetCommandTypeTimeoutStart ||
		type == NETCOMMANDTYPE_WRAPPER ||
		type == NETCOMMANDTYPE_HERO ||
		type == NETCOMMANDTYPE_FILE ||
		type == NETCOMMANDTYPE_FILEANNOUNCE ||
		type == NETCOMMANDTYPE_FILEPROGRESS ||
		type == NETCOMMANDTYPE_DISCONNECTFRAME ||
		type == kNetCommandTypeSaveGame);
}

// FUNCTION: BFME2 0x005812A0 size=36 name=?IsCommandSynchronized@@YA_NW4NetCommandType@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Bool IsCommandSynchronized(NetCommandType type)
{
	return (type == NETCOMMANDTYPE_GAMECOMMAND ||
		type == NETCOMMANDTYPE_FRAMEINFO ||
		type == NETCOMMANDTYPE_PLAYERLEAVE ||
		type == NETCOMMANDTYPE_DESTROYPLAYER ||
		type == kNetCommandTypeSaveGame);
}

// FUNCTION: BFME2 0x005812C4 size=84 name=?CommandRequiresDirectSend@@YA_NPAVNetCommandMsg@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Bool CommandRequiresDirectSend(NetCommandMsg *msg)
{
	NetCommandType type = msg->getNetCommandType();
	return (type == NETCOMMANDTYPE_DISCONNECTVOTE ||
		type == NETCOMMANDTYPE_DISCONNECTPLAYER ||
		type == NETCOMMANDTYPE_LOADCOMPLETE ||
		type == kNetCommandTypeTimeoutStart ||
		type == NETCOMMANDTYPE_HERO ||
		type == NETCOMMANDTYPE_FILE ||
		type == NETCOMMANDTYPE_FILEANNOUNCE ||
		type == NETCOMMANDTYPE_FILEPROGRESS ||
		type == NETCOMMANDTYPE_DISCONNECTFRAME ||
		type == NETCOMMANDTYPE_REQUESTGAMESPYSTATSAUTHKEY ||
		type == kNetCommandTypeGameSpyStatsAuthKey ||
		type == NETCOMMANDTYPE_INFORMPLAYERLEAVEFRAME ||
		type == NETCOMMANDTYPE_REQUESTFRAMEDATA ||
		type == NETCOMMANDTYPE_REQUESTPLAYERLEAVE);
}

// FUNCTION: BFME2 0x00581318 size=33 name=?Rva00581318Get@@YA_NPAVNetCommandMsg@@@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
Bool Rva00581318Get(NetCommandMsg *msg)
{
	NetCommandType type = msg->getNetCommandType();
	return (type == NETCOMMANDTYPE_REQUESTPLAYERLEAVE ||
		type == NETCOMMANDTYPE_ACKBOTH ||
		type == NETCOMMANDTYPE_ACKSTAGE1 ||
		type == NETCOMMANDTYPE_ACKSTAGE2);
}

// FUNCTION: BFME2 0x00581339 size=155 name=?ResolveIP@@YAIVAsciiString@@@Z evidence=X:map request (link (from standalone link 0cf3e833)) tier=B hypothesis:mm1-gap-unit
UnsignedInt ResolveIP(AsciiString host)
{
	if (host.getLength() == 0)
		return 0;

	if (isdigit(host.getCharAt(0)))
	{
		return ntohl(inet_addr(host.str()));
	}

	struct hostent *hostStruct = gethostbyname(host.str());
	if (hostStruct == NULL)
	{
		return 0;
	}
	return ntohl(*((UnsignedInt *)hostStruct->h_addr_list[0]));
}

// FUNCTION: BFME2 0x005813D4 size=471 name=?Rva005813D4Get@@YA?AVAsciiString@@H@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
AsciiString Rva005813D4Get(Int type)
{
	AsciiString str;
	if (type == NETCOMMANDTYPE_FRAMEINFO)
		str.set("NETCOMMANDTYPE_FRAMEINFO");
	else if (type == NETCOMMANDTYPE_REQUESTGAMESPYSTATSAUTHKEY)
		str.set("NETCOMMANDTYPE_REQUEST_GAMESPY_STATS_AUTHKEY");
	else if (type == kNetCommandTypeGameSpyStatsAuthKey)
		str.set("NETCOMMANDTYPE_GAMESPY_STATS_AUTHKEY");
	else if (type == NETCOMMANDTYPE_GAMECOMMAND)
		str.set("NETCOMMANDTYPE_GAMECOMMAND");
	else if (type == NETCOMMANDTYPE_PLAYERLEAVE)
		str.set("NETCOMMANDTYPE_PLAYERLEAVE");
	else if (type == NETCOMMANDTYPE_INFORMPLAYERLEAVEFRAME)
		str.set("NETCOMMANDTYPE_INFORMPLAYERLEAVEFRAME");
	else if (type == NETCOMMANDTYPE_REQUESTFRAMEDATA)
		str.set("NETCOMMANDTYPE_REQUESTFRAMEDATA");
	else if (type == NETCOMMANDTYPE_REQUESTPLAYERLEAVE)
		str.set("NETCOMMANDTYPE_REQUESTPLAYERLEAVE");
	else if (type == NETCOMMANDTYPE_DESTROYPLAYER)
		str.set("NETCOMMANDTYPE_DESTROYPLAYER");
	else if (type == NETCOMMANDTYPE_ACKBOTH)
		str.set("NETCOMMANDTYPE_ACKBOTH");
	else if (type == NETCOMMANDTYPE_ACKSTAGE1)
		str.set("NETCOMMANDTYPE_ACKSTAGE1");
	else if (type == NETCOMMANDTYPE_ACKSTAGE2)
		str.set("NETCOMMANDTYPE_ACKSTAGE2");
	else if (type == NETCOMMANDTYPE_KEEPALIVE)
		str.set("NETCOMMANDTYPE_KEEPALIVE");
	else if (type == NETCOMMANDTYPE_DISCONNECTCHAT)
		str.set("NETCOMMANDTYPE_DISCONNECTCHAT");
	else if (type == NETCOMMANDTYPE_CHAT)
		str.set("NETCOMMANDTYPE_CHAT");
	else if (type == NETCOMMANDTYPE_DISCONNECTKEEPALIVE)
		str.set("NETCOMMANDTYPE_DISCONNECTKEEPALIVE");
	else if (type == NETCOMMANDTYPE_DISCONNECTPLAYER)
		str.set("NETCOMMANDTYPE_DISCONNECTPLAYER");
	else if (type == NETCOMMANDTYPE_DISCONNECTVOTE)
		str.set("NETCOMMANDTYPE_DISCONNECTVOTE");
	else if (type == NETCOMMANDTYPE_PROGRESS)
		str.set("NETCOMMANDTYPE_PROGRESS");
	else if (type == NETCOMMANDTYPE_LOADCOMPLETE)
		str.set("NETCOMMANDTYPE_LOADCOMPLETE");
	else if (type == kNetCommandTypeTimeoutStart)
		str.set("NETCOMMANDTYPE_TIMEOUTSTART");
	else if (type == NETCOMMANDTYPE_WRAPPER)
		str.set("NETCOMMANDTYPE_WRAPPER");
	else if (type == NETCOMMANDTYPE_HERO)
		str.set("NETCOMMANDTYPE_HERO");
	else if (type == NETCOMMANDTYPE_FILE)
		str.set("NETCOMMANDTYPE_FILE");
	else if (type == NETCOMMANDTYPE_FILEANNOUNCE)
		str.set("NETCOMMANDTYPE_FILEANNOUNCE");
	else if (type == NETCOMMANDTYPE_FILEPROGRESS)
		str.set("NETCOMMANDTYPE_FILEPROGRESS");
	else if (type == NETCOMMANDTYPE_DISCONNECTFRAME)
		str.set("NETCOMMANDTYPE_DISCONNECTFRAME");
	else if (type == kNetCommandTypeSaveGame)
		str.set("NETCOMMANDTYPE_SAVE_GAME");
	else
		str.set("UNKNOWN");
	return str;
}
