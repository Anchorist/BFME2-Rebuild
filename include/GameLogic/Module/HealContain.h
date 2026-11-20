// HealContain.h: a contain that heals its occupants over time. SIZE 0xFC. The constructor calls OpenContain's and only
// re-installs the tables, so the class adds no members; xfer writes its version and defers to OpenContain::xfer. Its
// module data is HealContainModuleData (TimeForFullHeal at +0x98).
#pragma once
#ifndef BFME2_HEALCONTAIN_H
#define BFME2_HEALCONTAIN_H

#include "GameLogic/Module/OpenContain.h"
#include "GameLogic/Module/HealContainModuleData.h"

class HealContain : public OpenContain
{
public:
	HealContain(Thing *thing, const ModuleData *moduleData);

	const HealContainModuleData *getHealContainModuleData() const
	{
		return (const HealContainModuleData *)getModuleData();
	}

	virtual Bool containSlot06() { return true; }
	virtual NameKeyType getModuleNameKey() const;
	virtual UpdateSleepTime update();
	virtual ~HealContain();										// public: the destructor's retail name is the public ??1HealContain@@UAE@XZ

protected:
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);
protected:
	virtual void loadPostProcess() { OpenContain::loadPostProcess(); }	// slot 1: a jump to OpenContain's, shared with other classes
};
// SIZE 0xFC

typedef char HealContain_size[(sizeof(HealContain) == 0xFC) ? 1 : -1];

#endif
