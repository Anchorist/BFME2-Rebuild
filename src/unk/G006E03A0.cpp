// cl: /O2 /G6 /MD /D_CRTIMP=
#include "Apt/AptValue.h"
#include "Apt/Assert.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G006E03A0 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x006E03A0 size=75 name=?isLevelInst@AptValue@@QBE_NXZ evidence=X:map request (link (from standalone link 0cf3e833)) tier=B hypothesis:mm1-gap-unit
bool AptValue::isLevelInst() const
{
	if (!(this != 0)) {
		g_bfmeAptAssertAtE17734("this", "c:\\projects\\bfme2patch103\\bfme2\\code\\libraries\\source\\apt\\AptCIH.h", 0xd8);
		if (g_bfmeAptBreakOnAssertAtDDC01C) APT_ASSERT_BREAK();
	}
	return getVtblIndex() == 0x13 && !isUndefined();
}
// FUNCTION: BFME2 0x006E03F0 size=67 name=?wrapAngle@@YAMM@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
