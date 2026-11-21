// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004C81B7 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/DevastateSpecialPowerModuleData.h"
// FUNCTION: BFME2 0x004C81B7 size=17 name=?rva004C81B7@Rva004C81B7@@QAEXM@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
static const FieldParse s_devastateSpecialPowerModuleDataFieldParse[] =
{
	{ "Radius", INI::parseReal, 0, 0x7C },
	{ "FX", INI::parseFXList, 0, 0x80 },
	{ "TreeValueMultiplier", INI::parsePercentToReal, 0, 0x84 },
	{ "TreeValueTotalCap", INI::parseReal, 0, 0x88 },
	{ "FireWeapon", INI::parseAsciiString, 0, 0x8C },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004C81C8 size=27 name=?buildFieldParse@DevastateSpecialPowerModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void DevastateSpecialPowerModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	SpecialPowerModuleData::buildFieldParse(parse);
	parse.add(s_devastateSpecialPowerModuleDataFieldParse, 0);
}

