// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004AEF05 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/DetachableRiderUpdateModuleData.h"
#include "GameLogic/Weapon.h"
void Rva004AEB84Parse(INI *ini, void *instance, void *store, const void *userData);
static const FieldParse s_detachableRiderUpdateModuleDataFieldParse[] =
{
	{ "RiderSubObjects", INI::parseAsciiStringVector, 0, 0x14 },
	{ "RiderlessWeaponSlot", INI::parseLookupList, TheWeaponSlotTypeNamesLookupList, 0x20 },
	{ "RiderlessHordeFlees", INI::parseBool, 0, 0x24 },
	{ "DeathEntry", Rva004AEB84Parse, 0, 0x8 },
	{ "RemoveRiderlessFromHorde", INI::parseBool, 0, 0x25 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004AEF05 size=17 name=?buildFieldParse@DetachableRiderUpdateModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void DetachableRiderUpdateModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_detachableRiderUpdateModuleDataFieldParse, 0);
}

// FUNCTION: BFME2 0x004AEF16 size=13 name=?set@Rva004AEF16DwordSlot@@QAEXH@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
