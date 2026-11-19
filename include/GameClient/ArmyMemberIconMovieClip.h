#pragma once

#include <stddef.h>
#include "Apt/AptRef.h"
#include "GameClient/AptCallbackAdders.h"

class AptMovieClipFrame;
class Image;

namespace StrategicHUD
{
class ArmyMemberIconObserver;

// The constructor 0x5FCEA9 allocates its 0x38-byte Impl and installs the
// five-slot table at RVA 0x87A1BC. The destructor restores AptRefTarget's
// table at offset zero after freeing the observer list and Impl.
class ArmyMemberIconMovieClip : public AptRefTarget
{
public:
	class Impl;

	ArmyMemberIconMovieClip(AptMovieClipFrame *frame, const AsciiString &type);
	virtual ~ArmyMemberIconMovieClip();
	virtual void DoUpdate();
	virtual void notifyClicked();
	virtual void notifyRollOut();
	virtual void notifyRollOver();

private:
	// 0x5FCA00 walks the observer pointers while updating the saved index.
	_STL::vector<ArmyMemberIconObserver *> m_observers; // +0x08
	int m_nextObserver;                               // +0x14
	Impl *m_impl;                                     // +0x18
};

class ArmyMemberIconMovieClip::Impl
{
public:
	Impl(ArmyMemberIconMovieClip *owner, AptMovieClipFrame *frame, const AsciiString &type);
	~Impl();

	void Update();
	void SetPortraitImage(const Image *image);
	void SetTypeImage(const Image *image);
	void OnClicked(const char *path);
	void OnInitialized(const char *path);
	void OnRollOver(const char *path);
	void OnTypeRollOut(const char *path);
	void OnTypeRollOver(const char *path);

private:
	ArmyMemberIconMovieClip *m_owner; // +0x00, constructor 0x5FCB47
	AptMovieClipFrame *m_frame;      // +0x04, clip creation call at 0x5FCBBB
	int m_level;                     // +0x08
	AsciiString m_name;              // +0x0C
	AptCommandMapAdder m_commands;   // +0x10, cleanup at 0x5FCAC6
	AptCallbackAdders m_images;      // +0x1C, cleanup at 0x5FCABA
	const Image *m_portrait;         // +0x28, SetPortraitImage
	const Image *m_typeImage;        // +0x2C, SetTypeImage
	int m_quantity;                  // +0x30, quantity update 0x5FC85A
	unsigned char m_flags;           // +0x34, initialization and type rollover
};

typedef char ArmyMemberIconMovieClip_size[(sizeof(ArmyMemberIconMovieClip) == 0x1C) ? 1 : -1];
typedef char ArmyMemberIconMovieClip_Impl_size[(sizeof(ArmyMemberIconMovieClip::Impl) == 0x38) ? 1 : -1];
}
