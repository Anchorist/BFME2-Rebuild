// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004AD4F2 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/GloriousChargeUpdateModuleData.h"
// FUNCTION: BFME2 0x004AD4F2 size=43 name=??0GloriousChargeUpdateModuleData@@QAE@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
GloriousChargeUpdateModuleData::GloriousChargeUpdateModuleData()
	: m_bonusRadius(0.0f), m_speechDuration(0), m_updateInterval(0)
{
}

static const FieldParse s_gloriousChargeUpdateModuleDataFieldParse[] =
{
	{ "BonusRadius", INI::parseReal, 0, 0xC8 },
	{ "SpeechDuration", INI::parseDurationUnsignedInt, 0, 0xCC },
	{ "UpdateInterval", INI::parseDurationUnsignedInt, 0, 0xD0 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004AD51D size=27 name=?buildFieldParse@GloriousChargeUpdateModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void GloriousChargeUpdateModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	SpecialAbilityUpdateModuleData::buildFieldParse(parse);
	parse.add(s_gloriousChargeUpdateModuleDataFieldParse, 0);
}

