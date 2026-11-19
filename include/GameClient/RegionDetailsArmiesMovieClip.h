#pragma once

#include "Common/UnicodeString.h"
#include "GameClient/AptCallbackAdders.h"

namespace StrategicHUD
{
class RegionArmyIconSlot;

// Constructor 0x5EFD8F installs the single deleting-destructor table at
// RVA 0x878964 and allocates the distinct 0x40-byte Impl.
class RegionDetailsArmiesMovieClip
{
public:
	class Impl;

	RegionDetailsArmiesMovieClip(int level, const AsciiString &name, unsigned int playerColor);
	virtual ~RegionDetailsArmiesMovieClip();

private:
	Impl *m_impl;
};

class RegionDetailsArmiesMovieClip::Impl
{
public:
	Impl(int level, const AsciiString &name, unsigned int playerColor);
	~Impl();

	void OnRollOverCommandPoints(const char *path);
	void OnRollOutCommandPoints(const char *path);
	void PlayerColor(int, char *buffer, bool);
	void SetIconSlotCount(int count);
	void ShowArmyName(const UnicodeString &name);
	void HideArmyName();
	void ShowCommandPoints(int used, int available);
	void HideCommandPoints();
	void Update();

private:
	int m_level;                               // +0x00
	AsciiString m_name;                        // +0x04
	unsigned int m_playerColor;                // +0x08, constructor 0x5EF92D
	AptCommandMapAdder m_commands;              // +0x0C
	AptExternHandlerAdder m_externalHandlers;   // +0x18
	// 0x5EFE87 allocates a 0x40-byte icon slot. The vector stores
	// complete-object pointers and the slot's AptRefTarget is at +4.
	_STL::vector<AptRef<RegionArmyIconSlot> > m_iconSlots; // +0x24
	UnicodeString m_armyName;                   // +0x30, ShowArmyName
	int m_usedCommandPoints;                   // +0x34, ShowCommandPoints
	int m_availableCommandPoints;              // +0x38
	bool m_armyNameShown;                      // +0x3C
	bool m_commandPointsShown;                 // +0x3D, 0x5EF31D
	bool m_commandPointsOver;                  // +0x3E, rollover callbacks
};

typedef char RegionDetailsArmiesMovieClip_size[(sizeof(RegionDetailsArmiesMovieClip) == 8) ? 1 : -1];
typedef char RegionDetailsArmiesMovieClip_Impl_size[(sizeof(RegionDetailsArmiesMovieClip::Impl) == 0x40) ? 1 : -1];
}
