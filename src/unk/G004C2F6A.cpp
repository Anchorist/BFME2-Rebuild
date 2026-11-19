// cl: /O1 /EHs /EHc- /D_CRTIMP= /D_STLP_USE_MALLOC /D_STLP_USE_STATIC_LIB /D_STLP_NO_EXCEPTIONS
// stlport46
#include "GameLogic/Module/ProductionSpeedBonusModuleData.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G004C2F6A name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x004C2F6A size=124 name=?doSpecialPower@ProductionSpeedBonus@@UAEXH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x004C2FE6 size=98 name=??0ProductionSpeedBonusModuleData@@QAE@XZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit

ProductionSpeedBonusModuleData::ProductionSpeedBonusModuleData()
{
	m_numberOfFrames = 0;
	m_speedMultiplier = 0.0f;
	m_types.clear();
}
