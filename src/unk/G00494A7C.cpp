// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G00494A7C name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/WeaponModeSpecialPowerUpdateModuleData.h"
#include "GameLogic/Weapon.h"
static const FieldParse s_weaponModeSpecialPowerUpdateModuleDataFieldParse[] =
{
	{ "Duration", INI::parseDurationUnsignedInt, 0, 0x1C },
	{ "AttributeModifier", INI::parseAsciiString, 0, 0x18 },
	{ "LockWeaponSlot", INI::parseLookupList, TheWeaponSlotTypeNamesLookupList, 0x20 },
	{ "WeaponSetFlags", BitFlags<104>::parseFromINI, 0, 0x24 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x00494A7C size=27 name=?buildFieldParse@WeaponModeSpecialPowerUpdateModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void WeaponModeSpecialPowerUpdateModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	SpecialPowerUpdateModuleData::buildFieldParse(parse);
	parse.add(s_weaponModeSpecialPowerUpdateModuleDataFieldParse, 0);
}

