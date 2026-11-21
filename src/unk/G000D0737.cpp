// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G000D0737 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/W3DSailModelDrawModuleData.h"
// FUNCTION: BFME2 0x000D0737 size=61 name=??0W3DSailModelDrawModuleData@@QAE@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
W3DSailModelDrawModuleData::W3DSailModelDrawModuleData()
{
	m_maxRotationDegrees = 0.0f;
	m_blowingThresholdDegrees = 0.25f;
	m_aboutDamping = 0.05f;
}

static const FieldParse s_w3DSailModelDrawModuleDataFieldParse[] =
{
	{ "MaxRotationDegrees", INI::parseAngleReal, 0, 0x188 },
	{ "BlowingThresholdDegrees", INI::parseAngleReal, 0, 0x18C },
	{ "AboutDamping", INI::parseReal, 0, 0x190 },
	{ 0, 0, 0, 0 }
};

// FUNCTION: BFME2 0x000D0774 size=27 name=?buildFieldParse@W3DSailModelDrawModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
void W3DSailModelDrawModuleData::buildFieldParse(MultiIniFieldParse &parse)
{
	W3DModelDrawModuleData::buildFieldParse(parse);
	parse.add(s_w3DSailModelDrawModuleDataFieldParse, 0);
}

