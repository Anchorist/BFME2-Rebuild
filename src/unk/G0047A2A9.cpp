// stlport46
// cl: /O1
#include "Common/INI.h"
#include "GameLogic/Module/HordeContainModuleData.h"
#include "GameLogic/Module/AODHordeContainModuleData.h"

// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G0047A2A9 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x0047A2A9 size=13 name=?set@Rva0047A2A9ByteSlot@@QAEXE@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0047A2B6 size=43 name=?initialize@Rva0047A2B6Floats@@QAEPAV1@XZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0047A2E1 size=207 name=??0AODHordeContainModuleData@@QAE@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// Field parse table for AODHordeContainModuleData (decoded from retail image).
static const FieldParse s_aODHordeContainModuleDataFieldParse[] =
{
	{ "FrequencyScale", INI::parseReal, 0, 0x274 },
	{ "FrequencyRandomness", INI::parseReal, 0, 0x278 },
	{ "AmplitudeScale", INI::parseReal, 0, 0x27C },
	{ "FrequencyRandomness", INI::parseReal, 0, 0x278 },
	{ "AmplitudeRandomness", INI::parseReal, 0, 0x280 },
	{ "StillAmplitude", INI::parseReal, 0, 0x284 },
	{ "FrequencyScaleZ", INI::parseReal, 0, 0x288 },
	{ "FrequencyRandomnessZ", INI::parseReal, 0, 0x28C },
	{ "AmplitudeScaleZ", INI::parseReal, 0, 0x290 },
	{ "FrequencyRandomnessZ", INI::parseReal, 0, 0x28C },
	{ "AmplitudeRandomnessZ", INI::parseReal, 0, 0x294 },
	{ "StillAmplitudeZ", INI::parseReal, 0, 0x298 },
	{ "OathFulfilledZFactor", INI::parseReal, 0, 0x29C },
	{ "LargeUnitHeightFactor", INI::parseReal, 0, 0x2A0 },
	{ "LargeUnitMinHeight", INI::parseReal, 0, 0x2A4 },
	{ "LargeUnitMaxHeight", INI::parseReal, 0, 0x2A8 },
	{ "LargeUnitTimeout", INI::parseDurationUnsignedInt, 0, 0x2AC },
	{ "LargeUnitTailOff", INI::parseReal, 0, 0x2B0 },
	{ "ScatterSpeedFactor", INI::parseReal, 0, 0x2B4 },
	{ "ScatterRandomness", INI::parseReal, 0, 0x2B8 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x0047A3B0 size=27 name=?buildFieldParse@AODHordeContainModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void AODHordeContainModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	HordeContainModuleData::buildFieldParse(parse);
	parse.add(s_aODHordeContainModuleDataFieldParse, 0);
}

