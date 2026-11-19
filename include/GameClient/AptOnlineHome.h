// The online shell's home and message-of-the-day panel.
#pragma once

#include "Common/UnicodeString.h"
#include "GameClient/AptOnline.h"

class AptOnline::OnlineHome : public AptOnlineScreen
{
public:
	OnlineHome(AptOnline *screen);
	virtual ~OnlineHome();
	virtual void InitGadgets() {}
	virtual void Update();
	virtual int rva005A6582(int, int, unsigned char, int) { return 0; }
	virtual int GameWindowSystem(GameWindow *, unsigned int, unsigned int, unsigned int) { return 1; }
	virtual void slot6();

	void NumTickerFields(int query, char *result, bool set);
	void OfficialSite(const char *);
	void InitGadgets(const char *name, void *, GameWindow *window);
	void rva005B98E9();
	void OnOpened(const char *);
	void rva005B977B();

	GameWindow *m_messageOfDayList;
	UnicodeString m_messageOfDay;
};

typedef char AptOnlineHomeSizeCheck[sizeof(AptOnline::OnlineHome) == 0x68 ? 1 : -1];
