// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004AC5F5 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/DestroyEnvironmentUpdateModuleData.h"
// FUNCTION: BFME2 0x004AC5F5 size=32 name=?Rva004AC5F5@@YAHPAVObject@@@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x004AC615 size=20 name=??0DestroyEnvironmentUpdateModuleData@@QAE@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
static const FieldParse s_destroyEnvironmentUpdateModuleDataFieldParse[] =
{
	{ "StartTime", INI::parseDurationUnsignedInt, 0, 0x8 },
	{ "DestructionTime", INI::parseDurationUnsignedInt, 0, 0xC },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004AC629 size=17 name=?buildFieldParse@DestroyEnvironmentUpdateModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void DestroyEnvironmentUpdateModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_destroyEnvironmentUpdateModuleDataFieldParse, 0);
}

// FUNCTION: BFME2 0x004AC63A size=70 name=??0DestroyEnvironmentUpdate@@QAE@PAVThing@@PBVModuleData@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
