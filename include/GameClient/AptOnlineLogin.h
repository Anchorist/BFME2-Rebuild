// The Apt online sign-in panel. The shell allocates 0xE0 bytes and
// the native constructor builds the shared screen base and account preferences.
#pragma once

#include "Common/GameSpyLoginPreferences.h"
#include "GameClient/AptOnlineScreen.h"

class AptOnline;

class AptOnlineLogin : public AptOnlineScreen
{
public:
	explicit AptOnlineLogin(AptOnline *screen);
	virtual ~AptOnlineLogin();

	virtual void InitGadgets() {}
	virtual void Update();
	virtual int rva005A6582(int window, int message, unsigned char key, int flags);
	virtual int GameWindowSystem(GameWindow *window, unsigned int message, unsigned int data1, unsigned int data2);
	virtual void slot6();
	virtual bool slot7() { return false; }

	void InitGadgets(const char *name, void *data, GameWindow *window);
	void CheckLogin();
	void OnAccountDeleted(bool success);

private:
	GameSpyLoginPreferences m_preferences;
	GameWindow *m_emailCombo;
	GameWindow *m_nicknameCombo;
	GameWindow *m_passwordEntry;
	GameWindow *m_rememberInfo;
	unsigned int m_unk0xB4;
	GameWindow *m_countryList;
	int m_state;
	unsigned int m_boundGadgets;
	bool m_unk0xC4;
	bool m_unk0xC5;
	int m_unk0xC8;
	bool m_unk0xCC;
	bool m_unk0xCD;
	bool m_unk0xCE;
	bool m_unk0xCF;
	unsigned char m_unk0xD0[2];
	bool m_unk0xD2;
	unsigned int m_unk0xD4;
	AsciiString m_unk0xD8;
	bool m_unk0xDC;
};

typedef char AptOnlineLoginSizeCheck[sizeof(AptOnlineLogin) == 0xE0 ? 1 : -1];
