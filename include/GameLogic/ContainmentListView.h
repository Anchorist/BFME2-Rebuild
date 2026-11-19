#pragma once
#if defined(_STLPORT_VERSION)
#include <list>
#endif
#include "Common/GameType.h"
#include "GameLogic/ContainmentList.h"
class ContainmentListView
{
public:
 ~ContainmentListView() {}
#if defined(_STLPORT_VERSION)
 const ContainmentList &objects() const { return *m_items; }
 // 0x0036AE51 (map: ?rva0036AE51@Rva0036AE51ListView@@QAE?AV?$list@...@XZ, a COMDAT 40 bytes long): copies the viewed list and clears the view's first member; a view with a null first member copies the empty list at 0x00E0362C.
 _STL::list<Object *> toList();
#endif
 // Either the container interface or the tunnel-count interface. toList consumes this view.
 const void *m_owner;
 const ContainmentList *m_items;
};
#if defined(_STLPORT_VERSION)
extern ContainmentList g_emptyContainmentList;
inline _STL::list<Object *> ContainmentListView::toList()
{
	if (m_owner)
	{
		const ContainmentList &source = *m_items;
		m_owner = 0;
		return ContainmentList(source);
	}
	return ContainmentList(g_emptyContainmentList);
}
#endif
