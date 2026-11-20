// BuddyThread.h: the queue the lobby code uses to talk to the GameSpy buddy thread.
// Portions derived from Command & Conquer Generals and Command & Conquer Generals Zero Hour, (c) Electronic Arts Inc., GPL-3.0-or-later; see LICENSE and NOTICE.
#pragma once
#ifndef BFME2_BUDDYTHREAD_H
#define BFME2_BUDDYTHREAD_H

#include <stddef.h>
#include <string>
#include <queue>
#include "Common/GameType.h"
#include "WWLib/thread.h"
#include "WWLib/mutex.h"

enum { MAX_BUDDY_CHAT_LEN = 128 };

typedef int GPProfile;
typedef int GPEnum;
typedef int GPResult;
typedef int GPErrorCode;

class BuddyRequest
{
public:
	enum
	{
		BUDDYREQUEST_LOGIN,
		BUDDYREQUEST_RELOGIN,
		BUDDYREQUEST_LOGOUT,
		BUDDYREQUEST_MESSAGE,
		BUDDYREQUEST_LOGINNEW,
		BUDDYREQUEST_ADDBUDDY,
		BUDDYREQUEST_DELBUDDY,
		BUDDYREQUEST_OKADD,
		BUDDYREQUEST_DENYADD,
		BUDDYREQUEST_SETSTATUS,
		BUDDYREQUEST_DELETEACCT,
		BUDDYREQUEST_MAX
	} buddyRequestType;

	union
	{
		struct
		{
			GPProfile recipient;
			WideChar text[MAX_BUDDY_CHAT_LEN];
		} message;

		struct
		{
			char nick[31];
			char email[51];
			char password[31];
			Bool hasFirewall;
		} login;

		struct
		{
			GPProfile id;
			WideChar text[MAX_BUDDY_CHAT_LEN];
		} addbuddy;

		struct
		{
			GPProfile id;
		} profile;

		struct
		{
			GPEnum status;
			char statusString[256];
			char locationString[256];
		} status;

		unsigned char m_raw[0x2B4];
	} arg;
};
typedef char BuddyRequestSize[(sizeof(BuddyRequest) == 0x2B8) ? 1 : -1];

class BuddyResponse
{
public:
	enum
	{
		BUDDYRESPONSE_LOGIN,
		BUDDYRESPONSE_DISCONNECT,
		BUDDYRESPONSE_MESSAGE,
		BUDDYRESPONSE_REQUEST,
		BUDDYRESPONSE_STATUS,
		BUDDYRESPONSE_MAX
	} buddyResponseType;

	GPProfile profile;
	GPResult result;

	union
	{
		struct
		{
			UnsignedInt date;
			char nick[31];
			WideChar text[MAX_BUDDY_CHAT_LEN];
		} message;

		struct
		{
			char nick[31];
			char email[51];
			char countrycode[3];
			WideChar text[1025];
		} request;

		struct
		{
			GPResult result;
			GPErrorCode errorCode;
			char errorString[MAX_BUDDY_CHAT_LEN];
			GPEnum fatal;
		} error;

		struct
		{
			char nick[31];
			char email[51];
			char countrycode[3];
			char location[256];
			GPEnum status;
			char statusString[256];
		} status;
	} arg;
};
typedef char BuddyResponseSize[(sizeof(BuddyResponse) == 0x864) ? 1 : -1];

// Owning pointer holder used for thread synchronization locks (zeroes the pointer before delete).
template <class T>
class OwnedLockPtr
{
public:
	OwnedLockPtr() : m_lock(0) {}
	~OwnedLockPtr() { clear(); }
	void clear();
	void reset(T *newLock);

private:
	T *m_lock;
};

class BuddyThreadClass;

class GameSpyBuddyMessageQueueInterface
{
public:
	virtual ~GameSpyBuddyMessageQueueInterface() {}							// slot 0x00
	virtual void startThread() = 0;											// slot 0x04
	virtual void endThread() = 0;											// slot 0x08
	virtual Bool isThreadRunning() = 0;										// slot 0x0C
	virtual Bool isConnected() = 0;											// slot 0x10
	virtual Bool vslot14() = 0;												// slot 0x14 (isConnecting)
	virtual void addRequest(const BuddyRequest &request) = 0;				// slot 0x18
	virtual Bool getRequest(BuddyRequest &request) = 0;						// slot 0x1C
	virtual void addResponse(const BuddyResponse &response) = 0;			// slot 0x20
	virtual Bool getResponse(BuddyResponse &response) = 0;					// slot 0x24
	virtual Int getLocalProfileID() = 0;									// slot 0x28
	virtual const char *vslot2C() const = 0;								// slot 0x2C
	virtual const char *get() const = 0;									// slot 0x30
	static GameSpyBuddyMessageQueueInterface *createNewMessageQueue();
};

class GameSpyBuddyMessageQueue : public GameSpyBuddyMessageQueueInterface
{
public:
	GameSpyBuddyMessageQueue();
	virtual ~GameSpyBuddyMessageQueue();									// slot 0x00
	virtual void startThread();												// slot 0x04
	virtual void endThread();												// slot 0x08
	virtual Bool isThreadRunning();											// slot 0x0C
	virtual Bool isConnected();												// slot 0x10
	virtual Bool vslot14();													// slot 0x14
	virtual void addRequest(const BuddyRequest &request);					// slot 0x18
	virtual Bool getRequest(BuddyRequest &request);							// slot 0x1C
	virtual void addResponse(const BuddyResponse &response);				// slot 0x20
	virtual Bool getResponse(BuddyResponse &response);						// slot 0x24
	virtual Int getLocalProfileID();										// slot 0x28
	virtual const char *vslot2C() const;									// slot 0x2C
	virtual const char *get() const;										// slot 0x30

	MutexClass m_requestMutex;												// +0x04
	MutexClass m_responseMutex;												// +0x0C
	_STL::queue<BuddyRequest> m_requests;									// +0x14
	_STL::queue<BuddyResponse> m_responses;									// +0x3C
	BuddyThreadClass *m_thread;												// +0x64
	MutexClass m_threadMutex;												// +0x68
	OwnedLockPtr<MutexClass::LockClass> m_threadLock;						// +0x70
};
typedef char GameSpyBuddyMessageQueueSize[(sizeof(GameSpyBuddyMessageQueue) == 0x74) ? 1 : -1];

class BuddyThreadClass : public ThreadClass
{
public:
	BuddyThreadClass(MutexClass *mutex);
	virtual ~BuddyThreadClass() {}
	virtual void Thread_Function();

	void waitForThreadReady();

	Bool m_isNewAccount;													// +0x50
	Bool m_isConnecting;													// +0x51
	Bool m_isConnected;														// +0x52
	unsigned char m_pad0x53;												// +0x53
	Int m_profileID;														// +0x54
	Int m_lastErrorCode;													// +0x58
	Bool m_isDeleting;														// +0x5C
	unsigned char m_pad0x5D[3];												// +0x5D
	_STL::string m_nick;													// +0x60
	_STL::string m_email;													// +0x6C
	_STL::string m_password;												// +0x78
	_STL::string m_unk0x84;													// +0x84
	_STL::string m_unk0x90;													// +0x90
	MutexClass *m_networkLock;												// +0x9C
	CriticalSectionClass m_criticalSection;									// +0xA0
	OwnedLockPtr<CriticalSectionClass::LockClass> m_ownedLock;				// +0xA8
};
typedef char BuddyThreadClassSize[(sizeof(BuddyThreadClass) == 0xAC) ? 1 : -1];

extern GameSpyBuddyMessageQueueInterface *TheGameSpyBuddyMessageQueue;

#endif
