// The Apt loading screen combines the common progress indicator and map preview.
#pragma once

#include "GameClient/AptMapPreview.h"
#include "GameClient/LoadScreen.h"

class WindowLayout;

class AptLoadScreen : public LoadScreen
{
public:
	AptLoadScreen(void *loadingType);
	virtual ~AptLoadScreen();

	virtual void update(int percent);
	virtual void init(GameInfo *game);
	virtual void reset();
	virtual void processProgress(int player, int percent);

	void PlayerColor(int index, char *result, bool set);
	void GameLoadingType(int index, char *text, bool quiet);

	WindowLayout *m_layout;
	int m_loadingType;
	AptMapPreview m_mapPreview;
	GameInfo *m_game;
	void *m_owner;
	int m_slotMap[8];
	int m_progress[8];
	bool m_startSpotsShown;
};

typedef char AptLoadScreenSizeCheck[sizeof(AptLoadScreen) == 0xD4 ? 1 : -1];
