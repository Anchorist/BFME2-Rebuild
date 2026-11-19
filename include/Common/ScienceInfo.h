#pragma once
#include "Common/GameType.h"
#include "Common/Overridable.h"
#include "Common/Science.h"
#include "Common/UnicodeString.h"
#include <vector>

// The store resolves the final INI override before using a science record.
class ScienceInfo : public Overridable
{
public:
	ScienceType m_science;
	UnicodeString m_displayName;
	UnicodeString m_description;
	// playerHasPrereqsForScience accepts any group for which every science is known.
	_STL::vector<_STL::vector<ScienceType> > m_prerequisites;
	// getSciencePurchaseCost selects the second cost for multiplayer.
	Int m_sciencePurchasePointCost;
	Int m_multiplayerPurchasePointCost;
	// isScienceGrantable reads this flag from the resolved record.
	Bool m_grantable;
};
