#pragma once

#include <vector>

#include "Common/NameKeyGenerator.h"
#include "Common/SubsystemInterface.h"

class FXList;
class Object;

struct AttributeModifierEntry
{
	UnsignedByte m_unk0x00[0x14];
	// The store finds a modifier by its INI name key.
	NameKeyType m_nameKey;
	// The special-power preview adds positive durations to the current frame.
	Int m_duration;

	const FXList *rva0040327B(Object *object);
	const FXList *rva004032D3(Object *object);
};

class AttributeModifierStore : public SubsystemInterface
{
public:
	AttributeModifierStore();
	virtual ~AttributeModifierStore();

	virtual void init();
	virtual Bool attemptReload(Bool *needsRestart);
	virtual Bool attemptRefresh();
	virtual void reset() {}
	virtual void update() {}

	Int rva00214713(NameKeyType nameKey);
	Int getDuration(Int index);
	const FXList *getFX(Int index, Object *object);
	const FXList *getEndFX(Int index, Object *object);

private:
	_STL::vector<AttributeModifierEntry *> m_modifiers;
	// The constructor initializes a second vector whose element type is still unknown.
	UnsignedByte m_unk0x18[0xC];
};

// GameEngine's allocation includes both vectors and the subsystem base.
typedef char AttributeModifierStoreSizeCheck[sizeof(AttributeModifierStore) == 0x24 ? 1 : -1];

extern AttributeModifierStore *TheAttributeModifierStore;
