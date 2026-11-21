// cl: /O1
// stlport46
#include "Common/INI.h"
#include "GameLogic/Module/EmotionTrackerUpdateModuleData.h"
void iniParseObjectFilter(INI *ini, void *instance, void *store, const void *userData);
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004B235D name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// Field parse table for EmotionTrackerUpdateModuleData (decoded from retail image).
static const FieldParse s_emotionTrackerUpdateModuleDataFieldParse[] =
{
	{ "TauntAndPointDistance", INI::parseReal, 0, 0x8 },
	{ "TauntAndPointUpdateDelay", INI::parseDurationUnsignedInt, 0, 0xC },
	{ "TauntAndPointExcluded", iniParseObjectFilter, 0, 0x10 },
	{ "AfraidOf", iniParseObjectFilter, 0, 0x14 },
	{ "AlwaysAfraidOf", iniParseObjectFilter, 0, 0x18 },
	{ "PointAt", iniParseObjectFilter, 0, 0x1C },
	{ "HeroScanDistance", INI::parseReal, 0, 0x20 },
	{ "FearScanDistance", INI::parseReal, 0, 0x24 },
	{ "QuarrelProbability", INI::parsePercentToReal, 0, 0x28 },
	{ "IgnoreVeterancy", INI::parseBool, 0, 0x2C },
	{ "ImmuneToFearLevel", INI::parseInt, 0, 0x30 },
	{ "AddEmotion", EmotionTrackerUpdateModuleData::IniParseAddEmotion, 0, 0x0 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004B235D size=17 name=?buildFieldParse@EmotionTrackerUpdateModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void EmotionTrackerUpdateModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_emotionTrackerUpdateModuleDataFieldParse, 0);
}

