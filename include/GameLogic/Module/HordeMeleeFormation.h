// The formation policy for a horde's melee unit positions.
#pragma once

#include "Common/Coord3D.h"
#include "Common/Vector.h"
#include "GameLogic/Module/HordeMeleeBase.h"

class HordeMeleeFormationConfig;

// One unit of the formation: 0x54 bytes; its state word is at +0 (setUnitRotating 0x00584FBF stores 2, setUnitArrived 0x00584FEB stores 3).
struct HordeMeleeFormationUnit
{
	Int m_state;
	Coord3D m_attackPosition;  // +0x04: getUnitAttackPosition (0x00585017) copies it out
	unsigned char m_unk0x10[0xC];
	Bool m_needsNewAttackPos;  // +0x1C: set by setUnitNeedsNewAttackPos (0x0058619F), getUnitAttackPosition refuses a unit while it is set
	unsigned char m_unk0x1D[3];
	UnsignedInt m_unk0x20;	// compared with the logic frame by canUnitRotate
	unsigned char m_unk0x24[0x30];
};

class HordeMeleeFormation : public HordeMeleeBase
{
public:
	HordeMeleeFormation(HordeContain *horde, HordeMeleeFormationConfig *config);
	virtual ~HordeMeleeFormation();

	virtual void meleeSlot01(UnsignedInt count);
	virtual void meleeSlot02(UnsignedInt count);
	virtual void startMeleeAttack(Object *unit);
	virtual void meleeSlot04();
	virtual void updateMeleeAttack(Object *unit);
	virtual void notifyOfMemberDeath(Object *unit);
	virtual Bool isUnitMoving(Int index);
	virtual Bool isUnitRotating(Int index) const;
	virtual Bool canUnitRotate(Int index);
	virtual void setUnitRotating(Int index);
	virtual void setUnitArrived(Int index);
	virtual void setUnitNeedsNewAttackPos(Object *unit, Int index);
	virtual Bool getUnitAttackPosition(Int index, Coord3D *position);
	virtual void xfer(Xfer *xfer);

private:
	_STL::vector<HordeMeleeFormationUnit> m_units;
	Bool m_unk0x14;
	HordeMeleeFormationConfig *m_config;
};

typedef char HordeMeleeFormationSizeCheck[sizeof(HordeMeleeFormation) == 0x1C ? 1 : -1];
typedef char HordeMeleeFormationUnitSizeCheck[sizeof(HordeMeleeFormationUnit) == 0x54 ? 1 : -1];
