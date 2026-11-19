#pragma once

#include <map>
#include <vector>

#include "Common/ScienceInfo.h"
#include "Common/SubsystemInterface.h"

class Player;
class ScienceQueryInterface;

// Uses the same subsystem lifetime and reload callbacks as the other INI stores.
class ScienceStore : public SubsystemInterface
{
public:
	virtual ~ScienceStore();
	virtual void init();
	virtual Bool attemptReload(Bool *needsRestart);
	virtual Bool attemptRefresh();
	virtual void reset();
	virtual void update() {}

	int getSciencePurchaseCost(ScienceType) const;
	ScienceType getScienceFromInternalName(const AsciiString &) const;
	AsciiString getInternalNameForScience(ScienceType) const;
	bool getNameAndDescription(ScienceType, UnicodeString &, UnicodeString &) const;
	bool playerHasRootPrereqsForScience(const Player *, ScienceType) const;
	bool playerHasPrereqsForScience(const ScienceQueryInterface *, ScienceType) const;
	// Checks purchase points after checking the prerequisites.
	bool rva001FF4D3(ScienceQueryInterface *, ScienceType) const;
	bool isScienceGrantable(ScienceType) const;
	bool isValidScience(ScienceType) const;
	ScienceType friend_lookupScience(const char *) const;

private:
	// findScienceInfo resolves each entry's override before testing its science key.
	_STL::vector<ScienceInfo *> m_sciences;

	bool hasPrereqsMemoized(const Player *, ScienceType, _STL::map<ScienceType, bool> &) const;
	const ScienceInfo *findScienceInfo(ScienceType) const;
};

extern ScienceStore *TheScienceStore;

// Set by a successful attemptReload and cleared by attemptRefresh.
extern bool g_scienceReloaded;
