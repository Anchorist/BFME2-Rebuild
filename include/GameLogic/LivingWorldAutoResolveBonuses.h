#pragma once

#include "Common/GameType.h"

class INI;

// The native field table at 0x00839E58 parses the resource threshold and
// weapon and armor multipliers at +0, +4 and +8, respectively.
class LivingWorldAutoResolveResourceBonus
{
public:
	LivingWorldAutoResolveResourceBonus()
		: m_minimumResources(-1), m_weaponMultiplier(1.0f), m_armorMultiplier(1.0f) {}

	void parseBonusIniSubBlock(INI *ini);

	Int m_minimumResources;
	Real m_weaponMultiplier;
	Real m_armorMultiplier;
};

// The science-point table at 0x00839A78 uses the same layout and defaults
// with a MinSciencePurchasePointsForBonus threshold.
class LivingWorldAutoResolveSciencePurchasePointBonus
{
public:
	LivingWorldAutoResolveSciencePurchasePointBonus()
		: m_minimumSciencePurchasePoints(-1), m_weaponMultiplier(1.0f), m_armorMultiplier(1.0f) {}

	void parseBonusIniSubBlock(INI *ini);

	Int m_minimumSciencePurchasePoints;
	Real m_weaponMultiplier;
	Real m_armorMultiplier;
};
