#pragma once

#include <stddef.h>
#include "Common/GameType.h"
#include "GameClient/AptCallbackAdders.h"
#include "GameClient/InGameNotificationBox.h"

class DisplayString;
struct InGameNotification;

// 0x2A63ED allocates 0x54 bytes before calling 0x4E6C34. The constructor
// installs the five-slot table at RVA 0x862440. The nonvirtual destructor
// 0x4E6A9B restores the InGameNotificationBox pure table.
class InGameNotificationBoxMovieClip : public InGameNotificationBox
{
public:
	InGameNotificationBoxMovieClip();
	~InGameNotificationBoxMovieClip();

	virtual bool isNotificationEnabled() const;
	virtual void setNotificationEnabled(bool enabled);
	virtual void openNotification(const UnicodeString &text, const InGameNotificationData &data, int duration);
	virtual void DoClose();
	virtual int hasActiveNotification();

	void OnInitialized(unsigned int);

private:
	Int m_movieLevel;                        // +0x04, AptPlayer::RemoveLevel at 0x4E6AC6
	Int m_state;                             // +0x08, initialization and close callbacks
	AptCommandMapAdder m_commands;            // +0x0C, native cleanup 0x52413E
	AptExternHandlerAdder m_externalHandlers; // +0x18, native cleanup 0x5241B0
	AptCustomRenderAdder m_customRenderers;   // +0x24, native cleanup 0x524265
	AptCallbackAdders m_assets;               // +0x30, native cleanup 0x5242D7
	Real m_messageWidth;                      // +0x3C, ExternMessageWidth writes it at 0x4E680E
	InGameNotification *m_pendingNotification; // +0x40, installed by Open and moved at 0x4E722B
	InGameNotification *m_currentNotification; // +0x44, cleared by OnClosed at 0x4E6BED
	UnsignedInt m_openedAt;                   // +0x48, compared with the elapsed time at 0x4E6858
	DisplayString *m_displayString;           // +0x4C, allocated by DisplayStringManager slot 14
	Bool m_enabled;                           // +0x50, read at 0x578522 and set at 0x4E6B93
	Bool m_hasImage;                          // +0x51, 0x4E7096 tests the pending image before toggling it
};

typedef char InGameNotificationBoxMovieClip_size[(sizeof(InGameNotificationBoxMovieClip) == 0x54) ? 1 : -1];
