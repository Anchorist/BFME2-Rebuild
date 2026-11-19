// BloodthirstyUpdate.h: horde sacrifice ("bloodthirsty") update. SIZE 0x30.
// Target facts (old repo Code/GameEngine/Source/GameLogic/Object/Update/BloodthirstyUpdate.cpp):
// UpdateModule (0x20), the BloodthirstyUpdateInterface vptr at +0x20, then the
// sacrifice target +0x24, a second object id +0x28 and the kill count +0x2C.
// The constructor (0x0044E0AA) zeroes the three and wakes the module at once.
// xfer (0x0044E006): Version(1, 1), UpdateModule::xfer, both ids, the count.
// Module data: SacrificeFilter +0x08, ExperienceModifier +0x0C (1.0 by default),
// InitiateVoice +0x10 (8 bytes, index -1 by default) (field table VA 0x00C3F120).
#pragma once
#ifndef BFME2_BLOODTHIRSTYUPDATE_H
#define BFME2_BLOODTHIRSTYUPDATE_H

#include "Common/BitFlags11.h"
#include "GameLogic/Module/UpdateModule.h"
#include "GameLogic/Module/ModuleData.h"
#include "GameLogic/ObjectFilter.h"
#include "Common/Rva002390CB.h"

enum CommandSourceType;

class BloodthirstyUpdateModuleData : public ModuleData
{
public:
	BloodthirstyUpdateModuleData();
	virtual ~BloodthirstyUpdateModuleData();
	static void buildFieldParse(MultiIniFieldParse &p);

	ObjectFilter m_sacrificeFilter;		// 0x08
	Real m_experienceModifier;			// 0x0C
	Rva002390CB m_initiateVoice;		// 0x10
};
// SIZE 0x18

class BloodthirstyUpdateInterface
{
public:
	virtual void sacrificeHorde(Object *victim, CommandSourceType source) = 0;	// 0
	virtual void cancelSacrifice() = 0;										// 1
	virtual Bool rva0044E12F(Object *obj) = 0;								// 2
	virtual Bool isValidSacrifice(Object *obj) = 0;							// 3
	virtual void setSacrificeTargetID(ObjectID targetID) = 0;												// 4
	virtual void setSacrificeOwnerID(ObjectID ownerID) = 0;										// 5
	virtual ObjectID getSacrificeTargetID() = 0;												// 6
	virtual ObjectID getSacrificeOwnerID() = 0;												// 7
	virtual void addSacrifice(Object *victim) = 0;							// 8
	virtual Rva002390CB rva0044E2F7() const = 0;								// 9
};

class BloodthirstyUpdate : public UpdateModule, public BloodthirstyUpdateInterface
{
public:
	BloodthirstyUpdate(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual UpdateSleepTime update();

	// BehaviorModuleInterface slot 37 returns the bloodthirsty interface at +0x20.
	virtual BloodthirstyUpdateInterface *slot37() { return this; }

	virtual void sacrificeHorde(Object *victim, CommandSourceType source);
	virtual void cancelSacrifice();
	virtual Bool rva0044E12F(Object *obj);
	virtual Bool isValidSacrifice(Object *obj);
	virtual void setSacrificeTargetID(ObjectID targetID) { m_sacrificeID = targetID; }
	virtual void setSacrificeOwnerID(ObjectID ownerID) { m_sacrificeOwnerID = ownerID; }
	virtual ObjectID getSacrificeTargetID() { return m_sacrificeID; }
	virtual ObjectID getSacrificeOwnerID() { return m_sacrificeOwnerID; }
	virtual void addSacrifice(Object *victim);
	virtual Rva002390CB rva0044E2F7() const;

	const BloodthirstyUpdateModuleData *getBloodthirstyUpdateModuleData() const
	{
		return (const BloodthirstyUpdateModuleData *)m_moduleData;
	}

protected:
	virtual ~BloodthirstyUpdate();
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

private:
	ObjectID m_sacrificeID;		// 0x24
	ObjectID m_sacrificeOwnerID;	// +0x28. The sacrifice claimant ID assigned and read through interface slots 5 and 7.
	UnsignedInt m_kills;		// 0x2C
protected:
	virtual void loadPostProcess() { UpdateModule::loadPostProcess(); }	// retail slot 0x00497805: a jmp to UpdateModule's, ICF-folded across classes
public:
	virtual DisabledMaskType getDisabledTypesToProcess() const { return DisabledMaskType(DisabledMaskType::kInit, 3, 4); }	// UpdateModuleInterface slot 1: retail 0x004AE972 (DISABLED_HELD and DISABLED_PARALYZED)
};
// SIZE 0x30

#endif
