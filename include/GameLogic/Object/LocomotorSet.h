// LocomotorSet.h: the set of locomotors an AI update owns (AIUpdateInterface +0x1CC). SIZE 0x24, Snapshot-derived (its
// snapshot name is "LocomotorSet"). The members: the vector of Locomotor pointers at +4; the mask of valid locomotor
// surfaces at +0x10, the OR of every added template's Surfaces; two flags, +0x14 (the template's DownhillOnly) and +0x15
// (its ScalesWalls), set when an added template has them; two AsciiStrings at +0x18 and +0x1C that the destructor releases
// (their roles are not recovered); and a Real at +0x20, zero after construction. addLocomotor asks the locomotor store for
// a new locomotor, appends it and updates the mask and flags; clear deletes every locomotor, empties the vector and zeroes
// the mask and flags. WorldBuilder strings name addLocomotor, DoXfer, xferSelfAndCurLocoPtr and setLocomotorAndBaseSpeed;
// "clear" is the predecessor game's name, no string names it.
#pragma once
#ifndef BFME2_LOCOMOTORSET_H
#define BFME2_LOCOMOTORSET_H

#include <stddef.h>
#include "Common/GameType.h"
#include "Common/AsciiString.h"
#include "Common/Snapshot.h"
#include "Common/Vector.h"

class Locomotor;
class LocomotorTemplate;
class INI;
class ThingTemplate;

class LocomotorSet : public Snapshot
{
public:
	LocomotorSet();
	virtual ~LocomotorSet();

	void clear();
	void addLocomotor(const LocomotorTemplate *lt, Bool flag);
	void xferSelfAndCurLocoPtr(Xfer *xfer, Locomotor **loco);
	void setLocomotorAndBaseSpeed(INI *ini, ThingTemplate *tt);

protected:
	virtual void loadPostProcess() {}
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);		// the map spells it DoXfer

public:
	// The predecessor game's findLocomotor (the map files it under a placeholder class; AIUpdateInterface::chooseGoodLocomotorFromCurrentSet passes &m_locomotorSet as the receiver): the first locomotor whose template's Surfaces (+0x14) share a bit with t.
	Locomotor *findLocomotor(UnsignedInt t);
	_STL::vector<Locomotor *> m_locomotors;		// +0x04
	UnsignedInt m_validLocomotorSurfaces;		// +0x10
	Bool m_downhillOnly;						// +0x14
	Bool m_scalesWalls;							// +0x15
	AsciiString m_unk0x18;						// +0x18: released by the destructor
	AsciiString m_unk0x1C;						// +0x1C: released by the destructor
	Real m_unk0x20;								// +0x20
};

typedef char LocomotorSet_off_m_validLocomotorSurfaces[(offsetof(LocomotorSet, m_validLocomotorSurfaces) == 0x10) ? 1 : -1];
typedef char LocomotorSet_off_m_unk0x20[(offsetof(LocomotorSet, m_unk0x20) == 0x20) ? 1 : -1];
typedef char LocomotorSetSize[(sizeof(LocomotorSet) == 0x24) ? 1 : -1];

#endif
