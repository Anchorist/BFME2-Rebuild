// cl: /O1
// stlport46
#include "Common/INI.h"
#include "GameLogic/Module/RainOfFireUpdate.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004AC03D name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x004AC03D size=90 name=??0RainOfFireUpdateModuleData@@QAE@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// Field parse table for RainOfFireUpdateModuleData (decoded from retail image).
static const FieldParse s_rainOfFireUpdateModuleDataFieldParse[] =
{
	{ "StartRainTime", INI::parseDurationUnsignedInt, 0, 0x8 },
	{ "DarknessFadeTime", INI::parseDurationUnsignedInt, 0, 0xC },
	{ "RainEmitterHeight", INI::parsePositiveNonZeroReal, 0, 0x10 },
	{ "DarknessLevel", INI::parsePositiveNonZeroReal, 0, 0x14 },
	{ "JitterRadius", INI::parseReal, 0, 0x18 },
	{ "DPSMin", INI::parsePositiveNonZeroReal, 0, 0x1C },
	{ "DPSMax", INI::parsePositiveNonZeroReal, 0, 0x20 },
	{ "DPSRampupTime", INI::parseDurationReal, 0, 0x24 },
	{ "RainOffset", INI::parseCoord2D, 0, 0x28 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004AC097 size=17 name=?buildFieldParse@RainOfFireUpdateModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void RainOfFireUpdateModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_rainOfFireUpdateModuleDataFieldParse, 0);
}

// FUNCTION: BFME2 0x004AC0A8 size=135 name=??0RainOfFireUpdate@@QAE@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
