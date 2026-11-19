// The Apt input translator keeps the latest mouse events for click-through.
#pragma once

#include <stddef.h>
#include "Common/GameMessageTranslator.h"
#include "Common/ICoord2D.h"

class AptTranslator : public GameMessageTranslator
{
public:
	AptTranslator();
	virtual GameMessageDisposition translateGameMessage(const GameMessage *message);
	virtual ~AptTranslator();
	void rva00432AA2();
	void rva00432AC5();

private:
	struct MouseEvent
	{
		GameMessage::Type message;
		ICoord2D position;
		unsigned int modifiers;
		unsigned int timestamp;
		unsigned char flags;
	};

	bool m_buttonPending[4];
	MouseEvent m_mouseEvents[20];
	GameMessage::Type m_latestMouseEvent;
	bool m_ignoreNextMessage;
	int m_cursorMode;
	int m_pendingFrames[3];
	int m_captureFrames;

	friend struct AptTranslatorLayout;
};

struct AptTranslatorLayout
{
	typedef char EventSize[sizeof(AptTranslator::MouseEvent) == 0x18 ? 1 : -1];
	typedef char Events[offsetof(AptTranslator, m_mouseEvents) == 0x08 ? 1 : -1];
	typedef char Latest[offsetof(AptTranslator, m_latestMouseEvent) == 0x1E8 ? 1 : -1];
	typedef char Size[sizeof(AptTranslator) == 0x204 ? 1 : -1];
};
