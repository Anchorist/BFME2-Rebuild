// cl: /O1
#include "GameClient/GameWindow.h"
#include "GameClient/GadgetProgressBar.h"
#include "GameClient/WinInstanceData.h"
#include "GameClient/Image.h"
// Draw-state accessors for the gadget window drawing; see the note in O000A3367.cpp.
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G000A0C66 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x000A0C66 size=8 name=?getEnabledColor4@@YAIPAVGameWindow@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
unsigned int getEnabledColor4(GameWindow *window)
{
	return window->m_instData.m_enabledDrawData[4].color;
}
// FUNCTION: BFME2 0x000A0C6E size=11 name=?getEnabledBorderColor4@@YAIPAVGameWindow@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
unsigned int getEnabledBorderColor4(GameWindow *window)
{
	return window->m_instData.m_enabledDrawData[4].borderColor;
}
// FUNCTION: BFME2 0x000A0C79 size=11 name=?getEnabledImage5@@YAPBVImage@@PAVGameWindow@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
const Image * getEnabledImage5(GameWindow *window)
{
	return window->m_instData.m_enabledDrawData[5].image;
}
// FUNCTION: BFME2 0x000A0C84 size=11 name=?getEnabledImage6@@YAPBVImage@@PAVGameWindow@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
const Image * getEnabledImage6(GameWindow *window)
{
	return window->m_instData.m_enabledDrawData[6].image;
}
// FUNCTION: BFME2 0x000A0C8F size=11 name=?getDisabledColor4@@YAIPAVGameWindow@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
unsigned int getDisabledColor4(GameWindow *window)
{
	return window->m_instData.m_disabledDrawData[4].color;
}
// FUNCTION: BFME2 0x000A0C9A size=11 name=?getDisabledBorderColor4@@YAIPAVGameWindow@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
unsigned int getDisabledBorderColor4(GameWindow *window)
{
	return window->m_instData.m_disabledDrawData[4].borderColor;
}
// FUNCTION: BFME2 0x000A0CA5 size=11 name=?getDisabledImage5@@YAPBVImage@@PAVGameWindow@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
const Image * getDisabledImage5(GameWindow *window)
{
	return window->m_instData.m_disabledDrawData[5].image;
}
// FUNCTION: BFME2 0x000A0CB0 size=11 name=?getDisabledImage6@@YAPBVImage@@PAVGameWindow@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
const Image * getDisabledImage6(GameWindow *window)
{
	return window->m_instData.m_disabledDrawData[6].image;
}
// FUNCTION: BFME2 0x000A0CBB size=11 name=?getHiliteColor4@@YAIPAVGameWindow@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
unsigned int getHiliteColor4(GameWindow *window)
{
	return window->m_instData.m_hiliteDrawData[4].color;
}
// FUNCTION: BFME2 0x000A0CC6 size=11 name=?getHiliteBorderColor4@@YAIPAVGameWindow@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
unsigned int getHiliteBorderColor4(GameWindow *window)
{
	return window->m_instData.m_hiliteDrawData[4].borderColor;
}
// FUNCTION: BFME2 0x000A0CD1 size=11 name=?getHiliteImage5@@YAPBVImage@@PAVGameWindow@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
const Image * getHiliteImage5(GameWindow *window)
{
	return window->m_instData.m_hiliteDrawData[5].image;
}
// FUNCTION: BFME2 0x000A0CDC size=11 name=?getHiliteImage6@@YAPBVImage@@PAVGameWindow@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
const Image * getHiliteImage6(GameWindow *window)
{
	return window->m_instData.m_hiliteDrawData[6].image;
}
// FUNCTION: BFME2 0x000A0CFF size=35 name=?input@GameWindow@@UAE?AW4WindowMsgHandledType@@III@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
WindowMsgHandledType GameWindow::input(unsigned int msg, unsigned int mData1, unsigned int mData2)
{
	if (m_inputFunc)
		return m_inputFunc(this, msg, mData1, mData2);
	return MSG_IGNORED;
}
// FUNCTION: BFME2 0x000A0D22 size=24 name=?system@Rva000A12E6Window@@UAE?AW4WindowMsgHandledType@@III@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
WindowMsgHandledType GameWindow::system(unsigned int msg, unsigned int mData1, unsigned int mData2)
{
	return GadgetProgressBarSystem(this, msg, mData1, mData2);
}
