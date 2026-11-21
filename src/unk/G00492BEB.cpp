// cl: /O1 /arch:SSE
// stlport46
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G00492BEB name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "GameLogic/Module/WeaponFireSpecialAbilityUpdate.h"
#include "GameLogic/Module/AIUpdate.h"
#include "GameLogic/Object/Locomotor.h"
#include "GameLogic/Object.h"
#include "GameLogic/GameLogic.h"
// FUNCTION: BFME2 0x00492BEB size=110 name=?update@WeaponFireSpecialAbilityUpdate@@UAE?AW4UpdateSleepTime@@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
UpdateSleepTime WeaponFireSpecialAbilityUpdate::update()
{
	if (m_packingState == 2)
	{
		Object *obj = getObject();
		Object *target = TheGameLogic->findObjectByID(m_targetID);
		AIUpdateInterface *ai = obj->getAIUpdateInterface();
		if (target && ai)
		{
			Coord3D pos = *target->getPosition();
			Locomotor *loco = ai->m_curLocomotor;
			if (loco)
				loco->rotateObjTowardsPosition(obj, &pos, NULL);
		}
	}
	return SpecialAbilityUpdate::update();
}
