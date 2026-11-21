// cl: /O1
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004C3F48 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/WeaponChangeSpecialPowerModuleData.h"
#include "GameLogic/Module/WeaponChangeSpecialPowerModuleData.h"
#include "GameLogic/Module/ElvenWoodSpecialPowerModuleData.h"
// FUNCTION: BFME2 0x004C3F48 size=122 name=?Rva004C3F48_ParseNamedReal@INI@@SAXPAV1@PAX1PBX@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
static const FieldParse s_elvenWoodSpecialPowerModuleDataFieldParse[] =
{
	{ "ElvenGroveObject", INI::parseAsciiString, 0, 0x88 },
	{ "ElvenNumObjects", INI::parseInt, 0, 0x8C },
	{ "ElvenWoodObject", INI::Rva004C3F48_ParseNamedReal, 0, 0x0 },
	{ "ElvenWoodRadius", INI::parseReal, 0, 0x90 },
	{ "ElvenWoodFX", INI::parseFXList, 0, 0x94 },
	{ "ElvenWoodOCL", INI::parseObjectCreationList, 0, 0x98 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004C3FC2 size=27 name=?buildFieldParse@ElvenWoodSpecialPowerModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void ElvenWoodSpecialPowerModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	SpecialPowerModuleData::buildFieldParse(parse);
	parse.add(s_elvenWoodSpecialPowerModuleDataFieldParse, 0);
}

static const FieldParse s_weaponChangeSpecialPowerModuleDataFieldParse[] =
{
	{ "FlagsUsedForToggle", BitFlags<104>::parseFromINI, 0, 0x7C },
	{ "ToggleOnSleepFrames", INI::parseInt, 0, 0x8C },
	{ "ToggleOffSleepFrames", INI::parseInt, 0, 0x90 },
	{ "ToggleOnAttributeModifier", INI::parseAsciiString, 0, 0x94 },
	{ "ToggleOffAttributeModifier", INI::parseAsciiString, 0, 0x98 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004C3FDD size=27 name=?buildFieldParse@WeaponChangeSpecialPowerModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void WeaponChangeSpecialPowerModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	SpecialPowerModuleData::buildFieldParse(parse);
	parse.add(s_weaponChangeSpecialPowerModuleDataFieldParse, 0);
}

