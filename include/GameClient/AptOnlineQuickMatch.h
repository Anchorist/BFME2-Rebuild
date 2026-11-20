// The QuickMatch.apt sub-screen. The native constructor installs its ten-slot
// table after AptOnlineScreen. The allocation in the online shell is 0xA0 bytes.
#pragma once

#include <stddef.h>
#include "Common/QuickMatchPreferences.h"
#include "GameClient/AptOnline.h"

class AptOnlineShell;
class Image;
class PeerResponse;

class AptOnline::OnlineQuickMatch : public AptOnlineScreen
{
public:
	OnlineQuickMatch(AptOnline *screen);
	virtual ~OnlineQuickMatch();
	virtual void InitGadgets();
	virtual void Update();
	virtual int rva005A6582(int window, int message, unsigned char key, int flags);
	virtual int GameWindowSystem(GameWindow *, unsigned int, unsigned int, unsigned int) { return 1; }
	virtual void slot6();

	void StartSimple(const char *);
	void PlayGame(const char *);
	void OnFoundMovieDone(const char *);
	void WidenSearch(const char *);
	void Cancel(const char *);
	void rva005BA39F(int value);
	void InitGadgets(const char *name, void *data, GameWindow *window);
	void OnMatched(PeerResponse &response);

private:
	AptOnlineShell *getShell() const;
	void rva005BB5CE();
	void rva005BBF15();
	bool rva005BA626();
	bool rva005BA6EE();

	int m_state;
	QuickMatchPreferences m_prefs;
	bool m_preferencesReady;
	bool m_playRequested;
	bool m_foundMoviePlaying;
	unsigned int m_boundGadgets;
	GameWindow *m_colorCombo;
	GameWindow *m_playersCombo;
	GameWindow *m_sideCombo;
	GameWindow *m_pingCombo;
	GameWindow *m_ladderCombo;
	const Image *m_selectedImage;
	const Image *m_unselectedImage;
	int m_ladderTeamSize;

	friend struct AptOnlineQuickMatchLayout;
};

struct AptOnlineQuickMatchLayout
{
	typedef AptOnline::OnlineQuickMatch Screen;
	typedef char Preferences[offsetof(Screen, m_prefs) == 0x64 ? 1 : -1];
	typedef char Combos[offsetof(Screen, m_colorCombo) == 0x80 ? 1 : -1];
	typedef char LadderTeamSize[offsetof(Screen, m_ladderTeamSize) == 0x9C ? 1 : -1];
	typedef char Size[sizeof(Screen) == 0xA0 ? 1 : -1];
};
