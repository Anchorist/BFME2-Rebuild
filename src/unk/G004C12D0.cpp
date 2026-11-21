// cl: /O1
// stlport46
#include "Common/INI.h"
#include "GameLogic/Module/RespawnBodyModuleData.h"
#include "GameLogic/Module/ActiveBodyModuleData.h"
void iniParseObjectFilter(INI *ini, void *instance, void *store, const void *userData);
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004C12D0 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// Field parse table for RespawnBodyModuleData (decoded from retail image).
static const FieldParse s_respawnBodyModuleDataFieldParse[] =
{
	{ "PermanentlyKilledByFilter", iniParseObjectFilter, 0, 0x64 },
	{ "CanRespawn", INI::parseBool, 0, 0x68 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004C12D0 size=27 name=?buildFieldParse@RespawnBodyModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void RespawnBodyModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	ActiveBodyModuleData::buildFieldParse(parse);
	parse.add(s_respawnBodyModuleDataFieldParse, 0);
}

