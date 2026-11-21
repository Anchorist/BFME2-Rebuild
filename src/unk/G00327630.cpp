// cl: /O1
// Portions derived from Command & Conquer Generals Zero Hour, (c) Electronic Arts Inc., GPL-3.0-or-later; see LICENSE and NOTICE.
#include "GameClient/GadgetCheckBox.h"
#include "GameClient/GameWindow.h"
#include "GameClient/GameWindowManager.h"
#include "GameClient/WinInstanceData.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G00327630 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x00327630 size=396 name=?GadgetRadioButtonInput@@YA?AW4WindowMsgHandledType@@PAVGameWindow@@III@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x003277BC size=23 name=?GadgetRadioSetGroup@@YAXPAVGameWindow@@HH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x003277D3 size=38 name=?GadgetRadioSetSelection@@YAXPAVGameWindow@@_N@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x003277F9 size=248 name=?GadgetRadioButtonSystem@@YA?AW4WindowMsgHandledType@@PAVGameWindow@@III@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x003278F1 size=71 name=?GadgetRadioSetText@@YAXPAVGameWindow@@VUnicodeString@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00327938 size=438 name=?GadgetCheckBoxInput@@YA?AW4WindowMsgHandledType@@PAVGameWindow@@III@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00327AEE size=69 name=?GadgetCheckBoxSetChecked@@YAXPAVGameWindow@@_N@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void GadgetCheckBoxSetChecked(GameWindow *window, bool isChecked)
{
	WinInstanceData *instData = window->winGetInstanceData();
	if (isChecked)
		instData->m_state |= 0x4;
	else
		instData->m_state &= ~0x4;
	TheWindowManager->winSendSystemMsg(window->winGetOwner(), 0x4008, (unsigned int)window, 0);
}
// FUNCTION: BFME2 0x00327B33 size=19 name=?GadgetCheckBoxIsChecked@@YA_NPAVGameWindow@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
bool GadgetCheckBoxIsChecked(GameWindow *window)
{
	WinInstanceData *instData = window->winGetInstanceData();
	return (instData->m_state & 0x4) != 0;
}
// FUNCTION: BFME2 0x00327B46 size=142 name=?GadgetCheckBoxSystem@@YA?AW4WindowMsgHandledType@@PAVGameWindow@@III@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00327BD4 size=71 name=?GadgetCheckBoxSetText@@YAXPAVGameWindow@@VUnicodeString@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
