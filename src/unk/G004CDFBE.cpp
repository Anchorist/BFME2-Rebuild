// cl: /O1
// stlport46
#include "Common/INI.h"
#include "GameLogic/Module/ActivateModuleSpecialPowerModuleData.h"
#include "GameLogic/Module/SpecialAbilityUpdateModuleData.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/UnleashSpecialPowerModuleData.h"
void parseTriggerSpecialPower(INI *ini, void *instance, void *store, const void *userData);
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004CDFBE name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// Field parse table for ActivateModuleSpecialPowerModuleData (decoded from retail image).
static const FieldParse s_activateModuleSpecialPowerModuleDataFieldParse[] =
{
	{ "TriggerSpecialPower", parseTriggerSpecialPower, 0, 0x0 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004CDFBE size=27 name=?buildFieldParse@ActivateModuleSpecialPowerModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void ActivateModuleSpecialPowerModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	SpecialAbilityUpdateModuleData::buildFieldParse(parse);
	parse.add(s_activateModuleSpecialPowerModuleDataFieldParse, 0);
}

static const FieldParse s_unleashSpecialPowerModuleDataFieldParse[] =
{
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004CDFEB size=27 name=?buildFieldParse@UnleashSpecialPowerModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void UnleashSpecialPowerModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	SpecialAbilityUpdateModuleData::buildFieldParse(parse);
	parse.add(s_unleashSpecialPowerModuleDataFieldParse, 0);
}

