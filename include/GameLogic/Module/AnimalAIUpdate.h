// AnimalAIUpdate.h: the animal AI update module. SIZE 0x3FC: AIUpdateInterface and, after it, the one-slot AnimalAIInterface
// (a role name; the interface's retail name is not recovered) whose slot returns the module data's AfraidOfCastles byte.
// The constructor runs AIUpdateInterface's and installs the class tables. xfer saves a version, an ObjectID at +0x3E8, a Bool
// at +0x3F8, a Coord3D at +0x3EC and a Bool at +0x3F9, then AIUpdateInterface's data. makeStateMachine returns a new
// AIStateMachine.
#pragma once
#ifndef BFME2_ANIMALAIUPDATE_H
#define BFME2_ANIMALAIUPDATE_H

#include "GameLogic/Module/AIUpdate.h"

class AnimalAIInterface
{
public:
	virtual Bool isAfraidOfCastles() const = 0;	// slot 0
};
// SIZE 0x4

class AnimalAIUpdate : public AIUpdateInterface, public AnimalAIInterface
{
public:
	AnimalAIUpdate(Thing *thing, const ModuleData *moduleData);
	static Module *friend_newModuleInstance(Thing *thing, const ModuleData *moduleData);
	virtual ~AnimalAIUpdate();

	virtual NameKeyType getModuleNameKey() const;
	virtual Bool isAfraidOfCastles() const;
	virtual UpdateSleepTime update();
	virtual AnimalAIInterface *getAnimalAIInterface() { return this; }	// slot 96, a getter shared with other classes

protected:
	virtual void xfer(Xfer *xfer);
	virtual AIStateMachine *makeStateMachine();
	virtual void loadPostProcess() { AIUpdateInterface::loadPostProcess(); }	// slot 1: a forwarder to AIUpdateInterface's

	ObjectID m_unk0x3E8;									// +0x3E8
	Coord3D m_unk0x3EC;										// +0x3EC
	Bool m_unk0x3F8;										// +0x3F8
	Bool m_unk0x3F9;										// +0x3F9
protected:
	virtual const char *GetSnapshotName() const;	// slot 2 of the class table
};
// SIZE 0x3FC

#endif
