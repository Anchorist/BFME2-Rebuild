#pragma once
#include "Common/UnicodeString.h"
class GameFont;
class DisplayStringManager;
struct IRegion2D;
// DisplayString: one piece of UI text, kept in the DisplayStringManager's list through m_next and m_prev.
// The object is 0x14 bytes (constructor 0x0035897D, destructor 0x00358994); the derived W3D class,
// whose constructor is 0x00106088, starts its own members at +0x14. The virtual table (0x00815338) has
// 24 slots; the W3D table (0x007CF900) shows which base methods are pure. Slot 20 is an empty
// clip-region method, not a pure virtual. Names follow Zero Hour's DisplayString where the W3D bodies
// and callers agree with it; the color setters and the float scale and size setters are BFME additions.
// MSVC lists overloads in reverse declaration order, so the two-argument draw is slot 13.
class DisplayString {
    friend class DisplayStringManager;
public:
    DisplayString();
    virtual ~DisplayString();
    virtual void setText(UnicodeString);
    virtual UnicodeString getText() { return m_textString; }
    virtual int getTextLength();
    virtual void notifyTextChanged() {}
    virtual void reset();
    virtual void setFont(GameFont *font) { m_font=font; }
    virtual GameFont *getFont() { return m_font; }
    virtual void setWordWrap(int) = 0;
    virtual void setWordWrapCentered(bool) = 0;
    virtual void setColors(int,int) = 0; // W3D 0x00105DC0 sets the renderer's text and drop-shadow color arrays
    virtual void setTextColor(int *) = 0; // W3D 0x00105E05 sets the text color
    virtual void setDropColor(int *) = 0; // W3D 0x00105E35 sets the drop-shadow color
    virtual void draw(int,int,int,int) = 0;
    virtual void draw(int,int) = 0;
    virtual void getSize(int *,int *) = 0;
    virtual int getWidth(int=-1) = 0;
    virtual void setScale(float x,float y) = 0; // slot 17, inferred from W3D 0x00105FE4 and 0x00154320, which store the scale at renderer +0xB4/+0xB8 (default 1.0); Draw_Sentence 0x00155B00 applies separate X and Y scales
    virtual void setTargetSize(float width,float height) = 0; // slot 18, inferred from W3D 0x00106036 and 0x00154370, which store the target size at renderer +0xBC/+0xC0; 0x00155C93 and 0x00155CBE divide it by the text bounds to derive the scales
    virtual void setUseHotkey(bool,int) = 0;
    virtual void setClipRegion(IRegion2D *) {}
    virtual void removeLastChar();
    virtual void appendChar(unsigned short);
    virtual void appendString(const UnicodeString &);
    DisplayString *next() { return m_next; }
protected:
    UnicodeString m_textString;
    GameFont *m_font;
    DisplayString *m_next,*m_prev;
};
typedef char DisplayStringSizeCheck[sizeof(DisplayString)==0x14 ? 1 : -1];
