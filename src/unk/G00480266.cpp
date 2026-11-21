// cl: /O1
// stlport46
#include "Common/INI.h"
#include "GameLogic/Module/SlaughterHordeContainModuleData.h"
#include "GameLogic/Module/HordeGarrisonContainModuleData.h"
#include "Common/BitFlags.h"
void iniParseObjectFilter(INI *ini, void *instance, void *store, const void *userData);
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G00480266 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// Field parse table for SlaughterHordeContainModuleData (decoded from retail image).
static const FieldParse s_slaughterHordeContainModuleDataFieldParse[] =
{
	{ "CashBackPercent", INI::parsePercentToReal, 0, 0xD4 },
	{ "CanAlwaysEnter", iniParseObjectFilter, 0, 0xD8 },
	{ "StatusRequiredForCanAlwaysEnter", ObjectStatusMaskType::parseFromINI, 0, 0xDC },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x00480266 size=27 name=?buildFieldParse@SlaughterHordeContainModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void SlaughterHordeContainModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	HordeGarrisonContainModuleData::buildFieldParse(parse);
	parse.add(s_slaughterHordeContainModuleDataFieldParse, 0);
}

