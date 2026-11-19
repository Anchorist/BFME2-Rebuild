// The horde melee policy that keeps its members in place.
#pragma once

#include "Common/Vector.h"
#include "GameLogic/Module/HordeMeleeBase.h"

class HordeMeleeHoldGround : public HordeMeleeBase
{
public:
	HordeMeleeHoldGround(HordeContain *horde);
	virtual ~HordeMeleeHoldGround();

	virtual void meleeSlot01(UnsignedInt count);
	virtual void meleeSlot02(UnsignedInt count);
	virtual void startMeleeAttack(Object *unit);
	virtual void meleeSlot04() {}
	virtual void updateMeleeAttack(Object *unit);
	virtual void notifyOfMemberDeath(Object *) {}
	virtual Bool isUnitMoving(Int) { return false; }
	virtual Bool isUnitRotating(Int index) const;
	virtual Bool canUnitRotate(Int) { return true; }
	virtual void setUnitRotating(Int index);
	virtual void setUnitArrived(Int index);
	virtual void setUnitNeedsNewAttackPos(Object *, Int) {}
	virtual Bool getUnitAttackPosition(Int, Coord3D *) { return false; }
	virtual void xfer(Xfer *xfer);

	_STL::vector<Int> m_unitStates;
};
