// The GameSpy login profile. Native construction delegates to UserPreferences
// and adds the four account maps, followed by loading GameSpyLogin.ini.
#pragma once

#include <list>
#include "Common/UserPreferences.h"

class GameSpyLoginPreferences : public UserPreferences
{
public:
	GameSpyLoginPreferences();
	virtual ~GameSpyLoginPreferences();
	virtual bool write();
	virtual bool load(AsciiString filename);

	AsciiString getPasswordForEmail(AsciiString email);
	void deleteNick(const AsciiString &email, const AsciiString &nickname);
	void deleteClan(const AsciiString &email, const AsciiString &clan);

private:
	typedef _STL::map<AsciiString, _STL::list<AsciiString> > AccountListMap;

	PreferenceMap m_passwordsByEmail;  // +0x14
	PreferenceMap m_unk0x20;
	AccountListMap m_nicknamesByEmail;  // +0x2C
	AccountListMap m_clansByEmail;      // +0x38
};

typedef char GameSpyLoginPreferencesSizeCheck[sizeof(GameSpyLoginPreferences) == 0x44 ? 1 : -1];
