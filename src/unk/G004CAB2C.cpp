// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004CAB2C name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/AnimationSoundClientBehaviorModuleData.h"
void Rva004CA798Parse(INI *ini, void *instance, void *store);
static const FieldParse s_animationSoundClientBehaviorModuleDataFieldParse[] =
{
	{ "AnimationSound", (INIFieldParseProc)Rva004CA798Parse, 0, 0x0 },
	{ "MaxUpdateRangeCap", INI::parsePositiveNonZeroReal, 0, 0x14 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x004CAB2C size=17 name=?buildFieldParse@AnimationSoundClientBehaviorModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void AnimationSoundClientBehaviorModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	parse.add(s_animationSoundClientBehaviorModuleDataFieldParse, 0);
}

// FUNCTION: BFME2 0x004CAB3D size=33 name=?Rva004CAB3D_ParseVoicePriority@INI@@SAXPAV1@PAX1PBX@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x004CAB5E size=14 name=?get@Rva004CAB5EDivMovField@@QBEHXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
