// cl: /O1
#include "GameLogic/Module/HordeTransportContainDamageModuleData.h"
#include "Common/INI/FieldParse.h"

// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004BB0BB name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.

// The damage module adds no configurable fields of its own.
static const FieldParse s_hordeTransportContainDamageFields[] =
{
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004BB0BB size=17 name=?buildFieldParse@HordeTransportContainDamageModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void HordeTransportContainDamageModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_hordeTransportContainDamageFields, 0);
}
