// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004A53BF name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include <stddef.h>
#include "Common/INI.h"
#include "Common/INI/FieldParse.h"
#include "GameLogic/Module/DieMuxData.h"
#include "GameLogic/Module/RubbleRiseUpdateModuleData.h"
// FUNCTION: BFME2 0x004A53BF size=101 name=?parseFXList@RubbleRiseUpdateModuleData@@SAXPAVINI@@PAX1PBX@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x004A5424 size=98 name=?parseOCL@RubbleRiseUpdateModuleData@@SAXPAVINI@@PAX1PBX@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x004A5486 size=34 name=?buildFieldParse@RubbleRiseUpdateModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
static const FieldParse s_rubbleRiseUpdateModuleDataFieldParse[] =
{
	{ "MinRubbleRiseDelay", INI::parseDurationUnsignedInt, 0, offsetof(RubbleRiseUpdateModuleData, m_minRubbleRiseDelay) },
	{ "MaxRubbleRiseDelay", INI::parseDurationUnsignedInt, 0, offsetof(RubbleRiseUpdateModuleData, m_maxRubbleRiseDelay) },
	{ "MinBurstDelay", INI::parseDurationUnsignedInt, 0, offsetof(RubbleRiseUpdateModuleData, m_minBurstDelay) },
	{ "MaxBurstDelay", INI::parseDurationUnsignedInt, 0, offsetof(RubbleRiseUpdateModuleData, m_maxBurstDelay) },
	{ "RubbleRiseDamping", INI::parseReal, 0, offsetof(RubbleRiseUpdateModuleData, m_rubbleRiseDamping) },
	{ "RubbleHeight", INI::parseReal, 0, offsetof(RubbleRiseUpdateModuleData, m_rubbleHeight) },
	{ "MaxShudder", INI::parseReal, 0, offsetof(RubbleRiseUpdateModuleData, m_maxShudder) },
	{ "BigBurstFrequency", INI::parseInt, 0, offsetof(RubbleRiseUpdateModuleData, m_bigBurstFrequency) },
	{ "OCL", RubbleRiseUpdateModuleData::parseOCL, 0, 0 },
	{ "FXList", RubbleRiseUpdateModuleData::parseFXList, 0, 0 },
	{ 0, 0, 0, 0 }
};

void RubbleRiseUpdateModuleData::buildFieldParse(MultiIniFieldParse &p)
{
	p.add(s_rubbleRiseUpdateModuleDataFieldParse, 0);
	p.add(DieMuxData::getFieldParse(), offsetof(RubbleRiseUpdateModuleData, m_dieMuxData));
}

