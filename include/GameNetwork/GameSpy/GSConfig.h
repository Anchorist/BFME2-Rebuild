// Portions derived from Command & Conquer Generals and Command & Conquer Generals Zero Hour, (c) Electronic Arts Inc., GPL-3.0-or-later; see LICENSE and NOTICE.
#pragma once
#ifndef BFME2_GSCONFIG_H
#define BFME2_GSCONFIG_H

#include <list>
#include <vector>
#include <set>
#include "GameNetwork/GameSpy/GameSpyConfig.h"

class GameSpyConfig : public GameSpyConfigInterface
{
public:
	GameSpyConfig(AsciiString config);
	virtual ~GameSpyConfig() {}

	virtual _STL::list<AsciiString> getPingServers() { return m_pingServers; }
	virtual Int getNumPingRepetitions() { return m_pingReps; }
	virtual Int getPingTimeoutInMs() { return m_pingTimeout; }
	virtual Int getPingCutoffGood() { return m_pingCutoffGood; }
	virtual Int getPingCutoffBad() { return m_pingCutoffBad; }

	virtual _STL::list<AsciiString> getQMMaps() { return m_qmMaps; }
	virtual Int getQMBotID() { return m_qmBotID; }
	virtual Int getQMChannel() { return m_qmChannel; }
	virtual void setQMChannel(Int channel) { m_qmChannel = channel; }

	virtual Bool isPlayerVIP(Int id);
	virtual Bool getManglerLocation(Int index, AsciiString &host, UnsignedShort &port);

	virtual AsciiString getLeftoverConfig() { return m_leftoverConfig; }
	virtual Bool restrictGamesToLobby() { return m_restrictGamesToLobby; }

	virtual Int getTimeBetweenRetries() { return m_natRetryInterval; }
	virtual Int getMaxManglerRetries() { return m_natMaxManglerRetries; }
	virtual Int getRetryInterval() { return m_natManglerRetryInterval; }
	virtual Int getKeepaliveInterval() { return m_natKeepaliveInterval; }
	virtual Int getPortTimeout() { return m_natPortTimeout; }
	virtual Int getRoundTimeout() { return m_natRoundTimeout; }

protected:
	_STL::list<AsciiString> m_pingServers;		// +0x04
	Int m_pingReps;								// +0x08
	Int m_pingTimeout;							// +0x0C
	Int m_pingCutoffGood;						// +0x10
	Int m_pingCutoffBad;						// +0x14

	Int m_natRetryInterval;						// +0x18
	Int m_natMaxManglerRetries;					// +0x1C
	Int m_natManglerRetryInterval;				// +0x20
	Int m_natKeepaliveInterval;					// +0x24
	Int m_natPortTimeout;						// +0x28
	Int m_natRoundTimeout;						// +0x2C

	_STL::vector<AsciiString> m_manglerHosts;	// +0x30
	_STL::vector<UnsignedShort> m_manglerPorts;	// +0x3C

	_STL::list<AsciiString> m_qmMaps;			// +0x48
	Int m_qmBotID;								// +0x4C
	Int m_qmChannel;							// +0x50

	Bool m_restrictGamesToLobby;				// +0x54
	_STL::set<Int> m_vip;						// +0x58
	AsciiString m_leftoverConfig;				// +0x64
};
typedef char GameSpyConfigSize[(sizeof(GameSpyConfig) == 0x68) ? 1 : -1];

class SectionChecker
{
public:
	typedef _STL::list<const Bool *> SectionList;
	void addVar(const Bool *var);
	Bool isInSection();

protected:
	SectionList m_bools;
};

#endif
