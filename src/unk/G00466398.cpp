// cl: /O1 /D_BFME_RETAIL_TREE_INSERT_LAYOUT /D_STLP_USE_MALLOC /D_STLP_USE_STATIC_LIB /D_STLP_BFME_COPY_TRIVIAL_EXTERN /D_STLP_NO_EXCEPTIONS
// stlport46
#include <list>
#include "Common/TunnelTracker.h"
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G00466398 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x00466398 size=26 name=?getContainedItemsList@TunnelTracker@@QAE?AVContainmentListView@@XZ evidence=X:map request (link (from standalone link 0cf3e833)) tier=B hypothesis:mm1-gap-unit
ContainmentListView TunnelTracker::getContainedItemsList()
{
	ContainmentListView view;
	view.m_owner = (TunnelCountInterface *)this;
	view.m_items = &m_containList;
	return view;
}
