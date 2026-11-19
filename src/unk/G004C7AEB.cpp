// cl: /O1
#include "GameLogic/Module/UntamedAllegianceSpecialPower.h"
#include "GameLogic/Module/UntamedAllegianceSpecialPowerModuleData.h"
#include "Common/INI/FieldParse.h"
#include "Common/Xfer.h"

// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004C7AEB name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.

// Configuration inherits only the special-power fields.
static const FieldParse s_untamedAllegianceFields[] =
{
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004C7AEB size=27 name=?buildFieldParse@UntamedAllegianceSpecialPowerModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void UntamedAllegianceSpecialPowerModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	SpecialPowerModuleData::buildFieldParse(parse);
	parse.add(s_untamedAllegianceFields, 0);
}

// FUNCTION: BFME2 0x004C7B06 size=42 name=??0UntamedAllegianceSpecialPower@@QAE@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
UntamedAllegianceSpecialPower::UntamedAllegianceSpecialPower(Thing *thing, const ModuleData *moduleData)
	: SpecialPowerModule(thing, moduleData)
{
}

void UntamedAllegianceSpecialPower::xfer(Xfer *xfer)
{
	xfer->Version1();
	SpecialPowerModule::xfer(xfer);
}
