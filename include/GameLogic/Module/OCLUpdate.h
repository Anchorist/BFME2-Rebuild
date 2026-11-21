// OCLUpdate: the update module that creates its module data's object creation list at intervals. SIZE 0x2C: UpdateModule
// (0x20) and three members that xfer saves in this order: the next creation frame, the frame the timer started and the
// number of creations so far (version 2 and later). update decides whether a creation is due, creates the list at the
// object's position (or at the closest map edge point when the module data asks for it), and counts the creations against
// the module data's amount. xfer also makes one transfer through a slot this view cannot place.
#pragma once
#ifndef BFME2_O_C_L_UPDATE_H
#define BFME2_O_C_L_UPDATE_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/UpdateModule.h"

class Thing;
class ModuleData;
class Xfer;

// UpdateModule ends at 0x20; this class's members follow it.
typedef char OCLUpdate_base_size[(sizeof(UpdateModule) == 0x20) ? 1 : -1];

class OCLUpdate : public UpdateModule
{
public:
	OCLUpdate(Thing *thing, const ModuleData *moduleData);
	static Module *friend_newModuleInstance(Thing *thing, const ModuleData *moduleData);
	unsigned int getRemainingFrames() const;
	float getCountdownPercent() const;
	virtual NameKeyType getModuleNameKey() const;
	virtual const char *GetSnapshotName() const;
	virtual UpdateSleepTime update();
	UnsignedByte shouldCreate();		// the creation frame has come and the object is not under construction
	void setNextCreationFrame();	// restarts the timer with a random delay between MinDelay and MaxDelay

protected:
	virtual void xfer(Xfer *xfer);

public:
	UnsignedInt m_nextCreationFrame;                    // +0x20; xfer UnsignedInt
	UnsignedInt m_timerStartedFrame;                    // +0x24; xfer UnsignedInt
	Int m_currentCount;                            // +0x28; xfer Int (version 2 and later)
protected:
	virtual void loadPostProcess() { UpdateModule::loadPostProcess(); }	// slot 1: a jump to UpdateModule's
};
// SIZE 0x2C
typedef char OCLUpdate_size[(sizeof(OCLUpdate) == 0x2C) ? 1 : -1];
typedef char OCLUpdate_off_m_nextCreationFrame[(offsetof(OCLUpdate, m_nextCreationFrame) == 0x20) ? 1 : -1];
typedef char OCLUpdate_off_m_timerStartedFrame[(offsetof(OCLUpdate, m_timerStartedFrame) == 0x24) ? 1 : -1];
typedef char OCLUpdate_off_m_currentCount[(offsetof(OCLUpdate, m_currentCount) == 0x28) ? 1 : -1];

#endif
