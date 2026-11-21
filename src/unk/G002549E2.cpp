// cl: /O1
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G002549E2 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "GameLogic/Module/TransitionDamageFXModuleData.h"
#include "Common/INI.h"
// Module creators. Retail registers each module class with a static friend_newModuleInstance that allocates the
// module for a thing and its module data, and each module data class with a static friend_newModuleData that
// allocates the data and, when an INI block is open, fills it from the class's buildFieldParse table. The bodies
// below are those two shapes. A class whose creator is not here yet has no real header, lacks the constructor or
// buildFieldParse declaration, or did not compile with its current header (the usual cause is a pure virtual that
// the header does not override yet); its row stays unwritten.
// FUNCTION: BFME2 0x002549E2 size=84 name=?friend_newModuleData@TransitionDamageFXModuleData@@SAPAVModuleData@@PAVINI@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
ModuleData *TransitionDamageFXModuleData::friend_newModuleData(INI *ini)
{
	TransitionDamageFXModuleData *data = new TransitionDamageFXModuleData;
	if (ini)
		ini->initFromINIMultiProc(data, TransitionDamageFXModuleData::buildFieldParse);
	return data;
}
