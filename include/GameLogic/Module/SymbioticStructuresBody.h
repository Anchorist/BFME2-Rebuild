// The body that mirrors a host structure when it can connect to that host.
#pragma once
#ifndef BFME2_SYMBIOTIC_STRUCTURES_BODY_H
#define BFME2_SYMBIOTIC_STRUCTURES_BODY_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/ActiveBody.h"

class Thing;
class ModuleData;
class Xfer;

// ActiveBody ends at 0x100; this class's members follow it.
typedef char SymbioticStructuresBody_base_size[(sizeof(ActiveBody) == 0x100) ? 1 : -1];

class SymbioticStructuresBody : public ActiveBody
{
public:
	SymbioticStructuresBody(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual const char *GetSnapshotName() const;

protected:
	virtual void xfer(Xfer *xfer);
	virtual void loadPostProcess();	// override: loadPostProcess slot 1 at +0x0 (0x004C1170)
	virtual void mapLoadPostProcess(const Dict *properties);
	virtual void hostSlot23(Int);
	virtual Real getHostHealth();


	// BodyModuleInterface overrides (+0x10): each connects to the host body and forwards to it, or answers zero.
	virtual void attemptHealing(DamageInfo *damageInfo);					// 1, 0x004C0DD1
	virtual BodyDamageType getDamageState() const;						// 8, 0x004C0E68 (BODY_RUBBLE without a host)
	virtual const DamageInfo *getLastDamageInfo() const;				// 15, 0x004C0E46
	virtual unsigned int getLastDamageTimestamp() const;				// 16, 0x004C0F6F (-1 without a host)
	virtual unsigned int getLastHealingTimestamp() const;				// 17, 0x004C0F92 (-1 without a host)
	virtual ObjectID getAndClearLastAttacker();										// 18, 0x004C1006
	virtual unsigned char getFrontCrushed() const;							// 19, 0x004C1121 (retail's slot 20 holds the same body)
	virtual const FXList *getGrabFX() const;									// 29, 0x004C0E24
	virtual unsigned char isIndestructible() const;							// 34, 0x004C1147
	virtual Real estimateDamage(DamageInfoInput &input) const;			// 2, 0x004C1028
	virtual Real getHealthRatio() const;								// 5, 0x004C0D13 (refreshes the host indicators first)
	virtual Real getMaxHealth() const;									// 6, 0x004C105A
	virtual Real getInitialHealth() const;									// 7, 0x004C108B
	virtual Real getDamageScalar() const;								// 27, 0x004C0DF3
	virtual AsciiString getGrabObjectName() const;							// 28, 0x004C0ECE (empty without a host)
	virtual Real getGrabDamage() const;									// 30, 0x004C10F0
	virtual Real getDodgePercent() const;									// 35, 0x004C10BC
	virtual Bool rva004C2127(Object *) { return false; }
	virtual void rvaSlot39(BodyDamageType state);						// 39, 0x004C121B (rva0028FCD9 on the owner, then refreshHostDrawables)
	virtual void rvaSlot40(Real amount, Bool playHealingEffect);

	void synchronizeHostDamageState();

	Bool connectToHostBody() const;										// 0x004C0D4F (map: Rva004C0D4F): finds the host object's body from m_hostId and tells it this object's id
	void refreshHostDrawables() const;									// 0x004C0C52: flashes the drawables of the host and of this object (mode 5 on the one the local player does not own)

public:
	mutable ActiveBody *m_hostBody;                // +0x100; connectToHostBody stores the host object's body module here
	ObjectID m_hostId;                             // +0x104; xfer ObjectID: the host object
	BitFlags<21> m_fallbackArmorSetFlags;            // The armor flags returned without a host.
};
// SIZE 0x10C
typedef char SymbioticStructuresBody_size[(sizeof(SymbioticStructuresBody) == 0x10C) ? 1 : -1];
// The factory constructs this flag set, and getArmorSetFlags copies it as
// its four-byte result when no host body is available.
typedef char SymbioticStructuresBody_off_m_fallbackArmorSetFlags[(offsetof(SymbioticStructuresBody, m_fallbackArmorSetFlags) == 0x108) ? 1 : -1];
typedef char SymbioticStructuresBody_off_m_hostId[(offsetof(SymbioticStructuresBody, m_hostId) == 0x104) ? 1 : -1];

#endif
