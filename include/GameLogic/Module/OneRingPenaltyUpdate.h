#pragma once

#ifndef __BFME2_ONERINGPENALTYUPDATE_H_
#define __BFME2_ONERINGPENALTYUPDATE_H_

#include "UpdateModule.h"
#include "DieModuleInterface.h"

enum ObjectID;

class OneRingPenaltyUpdate : public UpdateModule, public DieModuleInterface
{
public:
    OneRingPenaltyUpdate(Thing *thing, const ModuleData *moduleData);
    virtual ~OneRingPenaltyUpdate();

    static Module *friend_newModuleInstance(Thing *thing, const ModuleData *moduleData);
    virtual NameKeyType getModuleNameKey() const;
    virtual UpdateSleepTime update();
    virtual void onDie(const DamageInfo *damageInfo);
    virtual DieModuleInterface *getDie() { return this; }

protected:
    virtual void loadPostProcess();
    virtual const char *GetSnapshotName() const;

    virtual void xfer(Xfer *xfer);

private:
    void rva00499AFD();
    void rva00499C35();
    void rva00499C46();
    void rva00499C6C();
    void rva00499D23();

    ObjectID m_pursuerID; // +0x24, the spawned object sent toward the wearer
    unsigned int m_ringWearStartFrame; // +0x28, starts the spawn timer
    float m_pursuitAngle; // +0x2C, directs the pursuer around the wearer
    unsigned int m_suppressionStartFrame; // +0x30, cleared when stealth is restored
};

#endif
