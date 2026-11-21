// cl: /O1
// stlport46
#include "Common/INI.h"
#include "GameLogic/Module/InvisibilityUpdateModuleData.h"
void Rva0026F28BParse(INI *ini, void *instance, void *store, const void *userData);
void Rva00438176Parse(INI *ini, void *instance, void *store, const void *userData);
void iniParseObjectFilter(INI *ini, void *instance, void *store, const void *userData);
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004A381C name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// Field parse table for InvisibilityUpdateModuleData (decoded from retail image).
static const FieldParse s_invisibilityUpdateModuleDataFieldParse[] =
{
	{ "InvisibilityNugget", Rva00438176Parse, 0, 0x8 },
	{ "UpdatePeriod", INI::parseDurationUnsignedInt, 0, 0xC0 },
	{ "RequiredUpgrades", Rva0026F28BParse, 0, 0xC4 },
	{ "ForbiddenUpgrades", Rva0026F28BParse, 0, 0x144 },
	{ "Broadcast", INI::parseBool, 0, 0x1C4 },
	{ "BroadcastObjectFilter", iniParseObjectFilter, 0, 0x1C8 },
	{ "BroadcastRange", INI::parseReal, 0, 0x1CC },
	{ "StartsActive", INI::parseBool, 0, 0x1D0 },
	{ "UnitSpecificSoundNameToUseAsVoiceMoveToStealthyArea", INI::parseAsciiString, 0, 0x1D4 },
	{ "UnitSpecificSoundNameToUseAsVoiceEnterStateMoveToStealthyArea", INI::parseAsciiString, 0, 0x1D8 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004A381C size=17 name=?buildFieldParse@InvisibilityUpdateModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void InvisibilityUpdateModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_invisibilityUpdateModuleDataFieldParse, 0);
}

