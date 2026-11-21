// cl: /O1
// stlport46
#include "Common/INI.h"
#include "GameLogic/Module/SpecialPowerModule.h"
#include "GameLogic/Module/CombineHordeSpecialPowerModuleData.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004C875E name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x004C875E size=75 name=?doSpecialPowerAtObject@RepairSpecialPower@@UAEXPAVObject@@I@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// Field parse table for CombineHordeSpecialPowerModuleData (decoded from retail image).
static const FieldParse s_combineHordeSpecialPowerModuleDataFieldParse[] =
{
	{ "ScanRange", INI::parseReal, 0, 0x7C },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004C87A9 size=27 name=?buildFieldParse@CombineHordeSpecialPowerModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void CombineHordeSpecialPowerModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	SpecialPowerModuleData::buildFieldParse(parse);
	parse.add(s_combineHordeSpecialPowerModuleDataFieldParse, 0);
}

