// The primary Apt message box uses the message movie's implementation pointer.
#pragma once

#include "GameClient/AptMessageBoxMovieClip.h"

class AptMessageBox : public AptMessageBoxMovieClip
{
public:
	AptMessageBox();
	virtual ~AptMessageBox();
};

typedef char AptMessageBoxSizeCheck[sizeof(AptMessageBox) == 0x08 ? 1 : -1];
