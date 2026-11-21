// cl: /O1
#include "GameLogic/Module/HordeDispatchSpecialPowerModuleData.h"
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/SpecialPowerModuleData.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004C888D name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x004C888D size=318 name=?doSpecialPower@CombineHordeSpecialPower@@UAEXI@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
static const FieldParse s_hordeDispatchSpecialPowerParseFieldParse[] =
{
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004C89CB size=27 name=?HordeDispatchSpecialPowerParse_25287D@@YAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void HordeDispatchSpecialPowerParse_25287D(MultiIniFieldParse &parse)
{
	SpecialPowerModuleData::buildFieldParse(parse);
	parse.add(s_hordeDispatchSpecialPowerParseFieldParse, 0);
}

