// cl: /O1
// stlport46
#include "Common/INI.h"
#include "GameLogic/Module/TaintSpecialPowerModuleData.h"
#include "GameLogic/Module/SpecialPowerModule.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004C487B name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// Field parse table for TaintSpecialPowerModuleData (decoded from retail image).
static const FieldParse s_taintSpecialPowerModuleDataFieldParse[] =
{
	{ "TaintObject", INI::parseAsciiString, 0, 0x7C },
	{ "TaintRadius", INI::parseReal, 0, 0x80 },
	{ "TaintFX", INI::parseFXList, 0, 0x84 },
	{ "TaintOCL", INI::parseObjectCreationList, 0, 0x88 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004C487B size=27 name=?buildFieldParse@TaintSpecialPowerModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void TaintSpecialPowerModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	SpecialPowerModuleData::buildFieldParse(parse);
	parse.add(s_taintSpecialPowerModuleDataFieldParse, 0);
}

