// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
#include "GameLogic/Module/GrabPassengerSpecialPower.h"
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/GrabPassengerSpecialPowerModuleData.h"
// object=G004C4F89 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
static const FieldParse s_grabPassengerSpecialPowerModuleDataFieldParse[] =
{
	{ "GrabRadius", INI::parseReal, 0, 0x7C },
	{ "AllowTree", INI::parseBool, 0, 0x80 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004C4F89 size=27 name=?buildFieldParse@GrabPassengerSpecialPowerModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void GrabPassengerSpecialPowerModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	SpecialPowerModuleData::buildFieldParse(parse);
	parse.add(s_grabPassengerSpecialPowerModuleDataFieldParse, 0);
}

// FUNCTION: BFME2 0x004C4FA4 size=42 name=??0GrabPassengerSpecialPower@@QAE@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
GrabPassengerSpecialPower::GrabPassengerSpecialPower(Thing *thing, const ModuleData *moduleData)
	: SpecialPowerModule(thing, moduleData)
{
}
