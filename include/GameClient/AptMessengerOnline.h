// The online messenger adds one byte to the common 0x2A0-byte screen.
// Native factory 0x5114F5 allocates 0x2A4 and construction 0x5AEF6B
// installs tables VA 0x872760 and VA 0x87275C over AptMessenger.
#pragma once

#include "GameClient/AptMessenger.h"

class AptMessengerOnline : public AptMessenger
{
public:
	explicit AptMessengerOnline(void *creationData);
	virtual ~AptMessengerOnline();

	virtual void vslot14();  // native tab-specific refresh at 0x5AF117
	virtual bool vslot15() const { return true; }  // native slot 15 at 0x50B5C6
	virtual ChatWindowsInGame *CreateChatWindow(int tab);

	void OnBttnInvite();
	void UpdatePlayerTabButtons();

private:
	bool m_unk0x2A0;
};

typedef char AptMessengerOnlineSizeCheck[sizeof(AptMessengerOnline) == 0x2A4 ? 1 : -1];
