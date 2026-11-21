// cl: /O1 /D_BFME_RETAIL_TREE_INSERT_LAYOUT /D_STLP_USE_MALLOC /D_STLP_USE_STATIC_LIB /D_STLP_BFME_COPY_TRIVIAL_EXTERN /D_STLP_NO_EXCEPTIONS
// stlport46
#include "GameClient/AptMpGameSetup.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G0043DA55 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x0043DA55 size=16 name=?rva005232d0@@YA_NHPBH@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0043DA65 size=24 name=?get@GameInfoTarget@@QAEPAVGameInfo@@XZ evidence=X:map request (link (from standalone link 0cf3e833)) tier=B hypothesis:mm1-gap-unit
GameInfo *GameInfoTarget::get()
{
	if (!slot1(m_gameInfo))
		m_gameInfo = 0;
	return m_gameInfo;
}
// FUNCTION: BFME2 0x0043DA7D size=10 name=?rva0043DA7D@Rva0041AC60@@QAEX_N@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0043DA87 size=14 name=?rva0043DA87@Rva0043DA87@@QBEHH@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0043DA95 size=8 name=?rva0043DA95@Rva0043DA95Owner@@QAEXXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0043DA9D size=8 name=?reset@Rva0043DA9D@@QAEXXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x0043DB23 size=26 name=?Rva0043DB23@@YAHPAVRva00222A8BTarget@@PAXPBD@Z evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
