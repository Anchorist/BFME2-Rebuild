// PingThread.h: GameSpy ICMP ping worker pool and queue (Zero Hour's PingerInterface/Pinger/PingThreadClass by role and member order,
// GPL-3.0-or-later; offsets, sizes, and the shutdown mutex are retail's).
// Portions derived from Command & Conquer Generals and Command & Conquer Generals Zero Hour, (c) Electronic Arts Inc., GPL-3.0-or-later; see LICENSE and NOTICE.
#pragma once
#ifndef BFME2_PINGTHREAD_H
#define BFME2_PINGTHREAD_H

#include <stddef.h>
#include <string>
#include <queue>
#include <map>
#include "Common/GameType.h"
#include "Common/AsciiString.h"
#include "WWLib/thread.h"
#include "WWLib/mutex.h"

class PingRequest
{
public:
	_STL::string hostname;		// +0x00
	Int repetitions;			// +0x0C
	Int timeout;				// +0x10
};
typedef char PingRequestSize[(sizeof(PingRequest) == 0x14) ? 1 : -1];

class PingResponse
{
public:
	_STL::string hostname;		// +0x00
	Int avgPing;				// +0x0C
	Int repetitions;			// +0x10
};
typedef char PingResponseSize[(sizeof(PingResponse) == 0x14) ? 1 : -1];

struct PingIpOptionInfo
{
	UnsignedByte ttl;
	UnsignedByte tos;
	UnsignedByte flags;
	UnsignedByte optionsSize;
	UnsignedByte *optionsData;
};

struct PingEchoReply
{
	UnsignedInt address;
	UnsignedInt roundTripTime;
	UnsignedShort dataSize;
	UnsignedShort reserved;
	void *data;
	PingIpOptionInfo options;
};
typedef char PingEchoReplySize[(sizeof(PingEchoReply) == 0x18) ? 1 : -1];

class PingerInterface
{
public:
	virtual ~PingerInterface() {}									// slot 0x00
	virtual void startThreads() = 0;								// slot 0x04
	virtual void endThreads() = 0;									// slot 0x08
	virtual Bool areThreadsRunning() = 0;							// slot 0x0C
	virtual void addRequest(const PingRequest &req) = 0;			// slot 0x10
	virtual Bool getRequest(PingRequest &req) = 0;					// slot 0x14
	virtual void addResponse(const PingResponse &resp) = 0;			// slot 0x18
	virtual Bool getResponse(PingResponse &resp) = 0;				// slot 0x1C
	virtual Bool arePingsInProgress() const = 0;					// slot 0x20
	virtual Int getPing(AsciiString hostname) = 0;					// slot 0x24
	virtual void clearPingMap() = 0;								// slot 0x28
	virtual AsciiString getPingString(Int timeout) = 0;				// slot 0x2C

	static PingerInterface *createNewPingerInterface();
};

class PingThreadClass : public ThreadClass
{
public:
	PingThreadClass(MutexClass *runMutex) : ThreadClass(0), m_runMutex(runMutex) {}
	virtual void Thread_Function();

private:
	Int doPing(UnsignedInt IP, Int timeout);

	MutexClass *m_runMutex;		// +0x50
};
typedef char PingThreadClassSize[(sizeof(PingThreadClass) == 0x54) ? 1 : -1];

class Pinger : public PingerInterface
{
public:
	enum { NumWorkerThreads = 10 };

	Pinger();
	virtual ~Pinger();

	virtual void startThreads();
	virtual void endThreads();
	virtual Bool areThreadsRunning();

	virtual void addRequest(const PingRequest &req);
	virtual Bool getRequest(PingRequest &req);

	virtual void addResponse(const PingResponse &resp);
	virtual Bool getResponse(PingResponse &resp);

	virtual Bool arePingsInProgress() const;
	virtual Int getPing(AsciiString hostname);

	virtual void clearPingMap();
	virtual AsciiString getPingString(Int timeout);

private:
	MutexClass m_requestMutex;					// +0x04
	MutexClass m_responseMutex;					// +0x0C
	MutexClass m_pingMapMutex;					// +0x14
	_STL::queue<PingRequest> m_requests;		// +0x1C
	_STL::queue<PingResponse> m_responses;		// +0x44
	Int m_requestCount;							// +0x6C
	Int m_responseCount;						// +0x70
	_STL::map<_STL::string, Int> m_pingMap;		// +0x74
	PingThreadClass *m_workerThreads[NumWorkerThreads];	// +0x80
	MutexClass m_threadMutex;					// +0xA8
	MutexClass::LockClass *m_threadLock;		// +0xB0
};
typedef char PingerSize[(sizeof(Pinger) == 0xB4) ? 1 : -1];

extern PingerInterface *ThePinger;

#endif
