// The movie frame owns its separate 0x1C-byte implementation. Retail
// 0x57C499 installs table VA 0x86F304 and stores the implementation at +4.
#pragma once

#include <stddef.h>
#include "Apt/AptRef.h"
#include "Common/AsciiString.h"
#include "GameClient/AptCallbackAdders.h"

class AptContentLoadedCallback;

class AptLoadMovieFrame
{
public:
	AptLoadMovieFrame(void *movieLevel, AsciiString frameName);
	virtual ~AptLoadMovieFrame();

	class Impl
	{
	public:
		void UnloadContent();
		void OnContentLoaded(const char *contentPath);
		void LoadContent(const AsciiString &contentPath, const AptRef<AptContentLoadedCallback> &callback);

		void *m_movieLevel;
		AsciiString m_frameName;
		AptCommandMapAdder m_commands;
		AptRef<AptContentLoadedCallback> m_onContentLoaded;
		bool m_contentLoaded;
	};

private:
	Impl *m_impl;
};

typedef char AptLoadMovieFrameSizeCheck[sizeof(AptLoadMovieFrame) == 0x08 ? 1 : -1];
typedef char AptLoadMovieFrameImplSizeCheck[sizeof(AptLoadMovieFrame::Impl) == 0x1C ? 1 : -1];
typedef char AptLoadMovieFrameCallbackOffset[offsetof(AptLoadMovieFrame::Impl, m_onContentLoaded) == 0x14 ? 1 : -1];
