// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G00458F7C name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/EnragedBehaviorModuleData.h"
// FUNCTION: BFME2 0x00458F7C size=22 name=??0EnragedBehaviorModuleData@@QAE@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
EnragedBehaviorModuleData::EnragedBehaviorModuleData()
{
	m_enragedLifeTimer = 99999.0f;
}

static const FieldParse s_enragedBehaviorModuleDataFieldParse[] =
{
	{ "EnragedLifeTimer", INI::parseReal, 0, 0x8 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x00458F92 size=17 name=?buildFieldParse@EnragedBehaviorModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void EnragedBehaviorModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_enragedBehaviorModuleDataFieldParse, 0);
}

