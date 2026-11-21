// cl: /O1
// stlport46
#include "Common/INI.h"
#include "GameLogic/Module/TeleportToCasterSpecialPowerModuleData.h"
#include "GameLogic/Module/SpecialAbilityUpdateModuleData.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004CD34E name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x004CD34E size=59 name=??0TeleportToCasterSpecialPowerModuleData@@QAE@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
TeleportToCasterSpecialPowerModuleData::TeleportToCasterSpecialPowerModuleData()
	: m_radius(0.0f)
	, m_minDestinationRadius(0.0f)
	, m_maxDestinationRadius(0.0f)
	, m_triggerFX(0)
	, m_targetFX(0)
{
}

// Field parse table for TeleportToCasterSpecialPowerModuleData (decoded from retail image).
static const FieldParse s_teleportToCasterSpecialPowerModuleDataFieldParse[] =
{
	{ "Radius", INI::parseReal, 0, 0xC8 },
	{ "MinDestinationRadius", INI::parseReal, 0, 0xCC },
	{ "MaxDestinationRadius", INI::parseReal, 0, 0xD0 },
	{ "TriggerFX", INI::parseFXList, 0, 0xD4 },
	{ "TargetFX", INI::parseFXList, 0, 0xD8 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004CD389 size=27 name=?buildFieldParse@TeleportToCasterSpecialPowerModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void TeleportToCasterSpecialPowerModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	SpecialAbilityUpdateModuleData::buildFieldParse(parse);
	parse.add(s_teleportToCasterSpecialPowerModuleDataFieldParse, 0);
}

