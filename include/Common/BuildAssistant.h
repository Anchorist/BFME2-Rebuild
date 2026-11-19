#pragma once

#include <list>

#include "Common/SubsystemInterface.h"

enum CanMakeType;
enum LegalBuildCode;
class Coord3D;
class Object;
class ObjectSellInfo;
class Player;
class Rva0039205C;
class ThingTemplate;

// The constructor initializes SubsystemInterface, then the sell list at +0xC.
class BuildAssistant : public SubsystemInterface
{
public:
	BuildAssistant();
	virtual ~BuildAssistant();

	virtual void init();
	virtual void reset();
	virtual void update();

	virtual Object *buildObjectNow(Object *builder, const ThingTemplate *what,
		const Coord3D *position, float angle, Player *owner);
	virtual bool rva00392DC0(Object *, const ThingTemplate *, const Coord3D *,
		Player *, unsigned int, Object **);
	virtual LegalBuildCode isLocationLegalToBuild(const Coord3D *, const ThingTemplate *,
		float, unsigned int, Object *, Player *);
	virtual bool isLocationClearOfObjects(const Coord3D *, const ThingTemplate *,
		float, Object *, unsigned int, Player *, bool);
	virtual bool rva0039361E(const Coord3D *, const ThingTemplate *, float, Object *, Player *);
	virtual void addBibs(const Coord3D *, const ThingTemplate *);
	virtual bool rva0039380F(Rva0039205C *, Object *, const Coord3D *, const Coord3D *, unsigned int);
	virtual bool rva0039321C(Rva0039205C *, Object *, Object *, unsigned int, bool);
	// The native entry returns zero. A caller has not established the return type.
	virtual void vfunc_0x58();
	virtual bool rva00391A70(const ThingTemplate *, const Object *);
	virtual CanMakeType canMakeUnit(Object *, const ThingTemplate *, int) const;
	virtual bool isPossibleToMakeUnit(Object *, const ThingTemplate *, int) const;
	virtual void sellObject(Object *);

	// Checks whether the factory's command set offers this template.
	bool offersBuildCommand(const ThingTemplate *builder, const ThingTemplate *whatToBuild);
	bool isRemovableForConstruction(Object *);

private:
	// canMakeUnit passes this record through the object visitor.
	struct ProductionCount
	{
		UnsignedInt count;
		const ThingTemplate *unitType;
	};
	friend int countInProduction(Object *, void *);

	_STL::list<ObjectSellInfo *> m_sellList;
	unsigned char m_unk0x10[0x18];
};

// GameEngine allocates 0x28 bytes before calling the constructor.
typedef char BuildAssistantSizeCheck[sizeof(BuildAssistant) == 0x28 ? 1 : -1];

extern BuildAssistant *TheBuildAssistant;
