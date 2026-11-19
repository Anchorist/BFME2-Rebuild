// The Apt display-string interface and its 0x30-byte W3D implementation.
// Tables 0x00BC93BC and 0x00BC9400 establish the three virtual slots.
// Their destructor chain restores the base table after releasing the W3D fields.
#pragma once
#ifndef BFME2_APT_DISPLAY_STRING_H
#define BFME2_APT_DISPLAY_STRING_H

#include "Common/GameType.h"
#include "Common/AsciiString.h"
#include "Common/UnicodeString.h"

class DisplayString;

class AptDisplayStringBase
{
public:
	virtual ~AptDisplayStringBase() {}
	virtual void SetText(const UnicodeString &text) = 0;
	virtual UnicodeString getText() = 0;
};

class W3DAptDisplayString : public AptDisplayStringBase
{
public:
	virtual ~W3DAptDisplayString();
	virtual void SetText(const UnicodeString &text);
	virtual UnicodeString getText();

private:
	AsciiString m_textLabel;
	DisplayString *m_displayString;
	Real m_left;
	Real m_top;
	Real m_right;
	Real m_bottom;
	Real m_textWidth;
	Real m_textHeight;
	Int m_textOptions;
	Int m_alignment;
	Bool m_scaleToScreen;
	Bool m_truncatedText;
	Bool m_hasDefaultDimensions;
};

typedef char AptDisplayStringBaseSizeCheck[sizeof(AptDisplayStringBase) == 0x04 ? 1 : -1];
typedef char W3DAptDisplayStringSizeCheck[sizeof(W3DAptDisplayString) == 0x30 ? 1 : -1];

#endif
