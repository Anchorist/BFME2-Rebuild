// The melee policy that lets horde members move independently.
#pragma once

#include <vector>
#include "Common/Coord3D.h"
#include "GameLogic/Module/HordeMeleeBase.h"

struct HordeMeleeSwarmUnit
{
	Int m_state;
	Coord3D m_attackPosition;  // +0x04: getUnitAttackPosition (0x00583D0A) copies it out
	Bool m_needsNewAttackPos;  // +0x10: set by setUnitNeedsNewAttackPos (0x00583CE0)
	unsigned char m_unk0x11[0x3];
	UnsignedInt m_rotateUntilFrame;  // +0x14: canUnitRotate (0x00583C4E) is true while the game frame (TheGameLogic +0x40) is below it
	UnsignedInt m_unk0x18;  // +0x18: xfer 0x00584A9B zero-initialises its local copy of it
};

class HordeMeleeSwarm : public HordeMeleeBase
{
public:
	HordeMeleeSwarm(HordeContain *horde);
	virtual ~HordeMeleeSwarm();

	virtual void meleeSlot01(UnsignedInt count);
	virtual void meleeSlot02(UnsignedInt count);
	virtual void startMeleeAttack(Object *unit);
	virtual void meleeSlot04();
	virtual void updateMeleeAttack(Object *unit);
	virtual void notifyOfMemberDeath(Object *) { m_membershipChanged = true; }
	virtual Bool isUnitMoving(Int index);
	virtual Bool isUnitRotating(Int index) const;
	virtual Bool canUnitRotate(Int index);
	virtual void setUnitRotating(Int index);
	virtual void setUnitArrived(Int index);
	virtual void setUnitNeedsNewAttackPos(Object *unit, Int index);
	virtual Bool getUnitAttackPosition(Int index, Coord3D *position);
	virtual void xfer(Xfer *xfer);

	std::vector<HordeMeleeSwarmUnit> m_units;
	Bool m_membershipChanged;
};

typedef char HordeMeleeSwarmUnitSizeCheck[sizeof(HordeMeleeSwarmUnit) == 0x1C ? 1 : -1];
