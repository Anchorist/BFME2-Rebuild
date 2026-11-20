// Squad.h: a list of object IDs the AI keeps for a task (Zero Hour's Squad; no MemoryPoolObject base here). SIZE 0x1C:
// a Snapshot, the ObjectID vector at +0x04 and the cache of live Object pointers at +0x10. Two out-of-line helpers refill
// the cache from the IDs: getAllObjectsKeepingIDs keeps every ID, getAllObjectsAndRemoveDead erases the IDs whose object is
// gone. getLiveObjects takes a Bool choosing between them and drops the unselectable objects.
#pragma once
#ifndef BFME2_SQUAD_H
#define BFME2_SQUAD_H

#include "Common/GameType.h"
#include "Common/Snapshot.h"
#include "Common/Vector.h"

class AIGroup;
class Object;
class Team;
class Xfer;

class Squad : public Snapshot
{
public:
	// Zero Hour's names (the Draft header this replaces carried them): Player::getSquadNumberForObject 0x002AA191 and
	// removeObjectFromHotkeySquad 0x002AA1BF call isOnSquad/removeObject on each of Player's ten squads, and
	// setCurrentlySelectedAIGroup 0x002ACC53 / processSelectTeamGameMessage 0x002ACAFB call clearSquad.
	bool isOnSquad(const Object *objToFind) const;
	void removeObject(Object *objectToRemove);
	void clearSquad();
	void addObject(Object *objectToAdd);
	void addObjectID(ObjectID objectID);
	const _STL::vector<Object *> &getAllObjectsAndRemoveDead();		// refills the cache, erasing the IDs of deleted objects
	const _STL::vector<Object *> &getAllObjectsKeepingIDs();		// refills the cache, keeping every ID
	const _STL::vector<Object *> &getLiveObjects(Bool pruneDeadIDs);	// the first helper when true, else the second, then drops the unselectable objects
	void squadFromAIGroup(const AIGroup *fromAIGroup, Bool clearSquadFirst);
	void squadFromTeam(const Team *fromTeam, Bool clearSquadFirst);
	void squadFromHordeRiders(Object *hordeObject, Bool clearSquadFirst);	// (role name): the object's horde interface lists its riders (slot 67)
	void aiGroupFromSquad(AIGroup *aiGroupToFill);

protected:
	virtual void loadPostProcess() {}								// slot 1: the shared `ret` 0x000B3FD0 (table 0x007F9D60)
	virtual void xfer(Xfer *xfer);
	virtual const char *GetSnapshotName() const;

	_STL::vector<ObjectID> m_objectIDs;								// +0x04
	_STL::vector<Object *> m_objectsCached;							// +0x10
};
// SIZE 0x1C

#endif
