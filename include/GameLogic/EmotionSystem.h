#pragma once

#include "Common/SubsystemInterface.h"
#include "Common/Vector.h"

class EmotionTrackerUpdateEntry;
class Object;

// 0x0022EF95 constructs the 0x30-byte subsystem. Constructor 0x00426402
// builds SubsystemInterface and three vectors, then installs table 0x0083C350.
class EmotionSystem : public SubsystemInterface
{
public:
	EmotionSystem();	// 0x00426402
	virtual ~EmotionSystem();	// 0x0042643D, deleting 0x00426556

	virtual void init();	// slot 1, 0x00426572
	virtual Bool attemptReload(Bool *needsRestart);	// slot 4, 0x004263CA
	virtual Bool attemptRefresh();	// slot 5, 0x00426378
	virtual void reset();	// slot 9, same clear routine as init
	virtual void update() {}	// slot 10, empty 0x000B3FD0

	EmotionTrackerUpdateEntry *findNugget(const AsciiString &name);	// 0x004264F4
	void AddEmotionNuggetTemplate(EmotionTrackerUpdateEntry *entry);	// 0x00426580
	void RegisterScaryObject(Object *object);	// 0x004265D9

private:
	_STL::vector<EmotionTrackerUpdateEntry *> m_templates;	// +0x0C, findNugget and AddEmotionNuggetTemplate
	_STL::vector<EmotionTrackerUpdateEntry *> m_unk0x18;	// destructor deletes each entry via 0x004DC9ED
	_STL::vector<ObjectID> m_scaryObjectIDs;	// +0x24, RegisterScaryObject adds Object +0x74
};

typedef char EmotionSystem_size[(sizeof(EmotionSystem) == 0x30) ? 1 : -1];
