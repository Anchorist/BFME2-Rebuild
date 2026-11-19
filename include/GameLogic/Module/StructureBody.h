// The active-body subclass used by structures.
#pragma once
#ifndef BFME2_STRUCTURE_BODY_H
#define BFME2_STRUCTURE_BODY_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/ActiveBody.h"

class Thing;
class Object;
class ModuleData;
class Xfer;

// ActiveBody ends at 0x100; this class's members follow it.
typedef char StructureBody_base_size[(sizeof(ActiveBody) == 0x100) ? 1 : -1];

class StructureBody : public ActiveBody
{
public:
	StructureBody(Thing *thing, const ModuleData *moduleData);
	void setConstructorObject(Object *obj);					// 0x004C09A1 (Zero Hour's name)
	ObjectID getConstructorObjectID() { return m_constructorObjectID; }
	virtual NameKeyType getModuleNameKey() const;

protected:
	virtual void loadPostProcess() { ActiveBody::loadPostProcess(); }	// slot 1: retail 0x004C202F, a jmp to ActiveBody's (0x004BF40F), ICF-folded across the ActiveBody subclasses
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

public:
	ObjectID m_constructorObjectID;               // +0x100; xfer ObjectID; the object that built this structure (Zero Hour StructureBody::m_constructorObjectID)
};
// SIZE 0x104
typedef char StructureBody_size[(sizeof(StructureBody) == 0x104) ? 1 : -1];
typedef char StructureBody_off_m_constructorObjectID[(offsetof(StructureBody, m_constructorObjectID) == 0x100) ? 1 : -1];

#endif
