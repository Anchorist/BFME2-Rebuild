// cl: /O1
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G002885EC name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/Overridable.h"
// FUNCTION: BFME2 0x002885EC size=7 name=?get@Rva002885ECByteField@@QBEEXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x002885F3 size=7 name=?get@Rva002885F3ByteField@@QBEEXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00288609 size=24 name=?friend_getFinalOverride@Overridable@@QBEPBV1@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
const Overridable *Overridable::friend_getFinalOverride() const
{
	if (m_nextOverride)
		return m_nextOverride->friend_getFinalOverride();
	return this;
}
