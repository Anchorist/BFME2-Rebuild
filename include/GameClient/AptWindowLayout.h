// An Apt movie hosted by a WindowLayout. Native constructor 0x40FDD1
// initializes the layout first, then adds the movie window and a lifecycle flag.
#pragma once

#include "GameClient/WindowLayout.h"

class _bfme_AptGameWindow;

class AptWindowLayout : public WindowLayout
{
public:
	explicit AptWindowLayout(GameWindow *parent);
	virtual ~AptWindowLayout();

	virtual void runInit(void *data);
	virtual void runUpdate(void *data);
	virtual void runShutdown(void *data);

private:
	_bfme_AptGameWindow *m_aptWindow;  // +0x24
	bool m_initialized;              // +0x28, set in runInit, cleared in runShutdown
};

typedef char AptWindowLayoutSizeCheck[sizeof(AptWindowLayout) == 0x2C ? 1 : -1];
