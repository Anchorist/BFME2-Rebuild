// Dynamic portals expose the die and creation interfaces at +0x1C and +0x20.
// The constructor at 0x00460B6C installs their base tables before the leaf
// tables. Behavior slots 3 and 7 return those complete-object offsets.
#pragma once
#ifndef BFME2_DYNAMIC_PORTAL_BEHAVIOUR_H
#define BFME2_DYNAMIC_PORTAL_BEHAVIOUR_H

#include <stddef.h>
#include "GameLogic/Module/CreateModule.h"
#include "GameLogic/Module/DieModuleInterface.h"
#include "GameLogic/Module/UpgradeModule.h"

class ModuleData;
class Object;
class Thing;
class Waypoint;
class Xfer;

class DynamicPortalBehaviour : public UpgradeModule,
	public DieModuleInterface,
	public CreateModuleInterface
{
public:
	DynamicPortalBehaviour(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual void upgradeImplementation();
	virtual void mapLoadPostProcess(const Dict *properties);

	virtual CreateModuleInterface *getCreate() { return this; }
	virtual DieModuleInterface *getDie() { return this; }

	virtual void onDie(const DamageInfo *damage);
	virtual void onCreate() {}							// shared empty body 0x000B3FD0
	virtual void onBuildComplete();
	virtual void vslot02() {}							// shared empty body 0x000B3FD0
	virtual Bool shouldDoOnBuildComplete() const { return true; }	// 0x0050B5C6

	static Module *rva004608E0(Object *obj);			// looks up the portal module on obj
	void rva0046094C();								// called by the siege deploy special power

protected:
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);
	virtual ~DynamicPortalBehaviour();
	virtual void loadPostProcess();
	virtual void upgradeRemovalImplementation();

public:
	// xfer 0x004609BC walks these six pointers, transferring each Waypoint's
	// ID from +4 and resolving the ID back through the terrain system.
	Waypoint *m_waypoints[6];
	Bool m_unk0x3C;
	Bool m_wasDestroyed;							// onDie 0x00460A85 sets this; onBuildComplete clears it

};

typedef char DynamicPortalWaypointOffset[(offsetof(DynamicPortalBehaviour, m_waypoints) == 0x24) ? 1 : -1];
typedef char DynamicPortalBehaviourSize[(sizeof(DynamicPortalBehaviour) == 0x40) ? 1 : -1];

#endif
