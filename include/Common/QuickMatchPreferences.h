// QuickMatchPreferences.h: the quick-match lobby's settings file (a UserPreferences with typed
// accessors that store their values as decimal strings). SIZE 0x14, no members of its own.
//
// Target facts (retail game.dat): the constructor 0x005DF1A3 calls UserPreferences' constructor
// 0x003B1FF1, stores the table 0x00C776DC (the thirteen UserPreferences slots with its own deleting
// destructor 0x005DF187 in slot 0) and loads "%s\QMPref%d.ini" (VA 0x00C77710; arguments "Online Files"
// and the local profile id) through UserPreferences::load(AsciiString) 0x003B1A09. The destructor
// 0x005DF17C restores the table and jumps to ~UserPreferences 0x003B1F65. The accessors read the
// map base at +4 (find 0x001F8437) or go through the virtual getInt/setInt (slots 6 and 11).
#pragma once
#ifndef BFME2_QUICKMATCHPREFERENCES_H
#define BFME2_QUICKMATCHPREFERENCES_H

#include "Common/UserPreferences.h"

class QuickMatchPreferences : public UserPreferences
{
public:
	QuickMatchPreferences();													// 0x005DF1A3
	virtual ~QuickMatchPreferences();

	void setColor(Int val);
	Int getColor();
	void setSide(Int val);
	Int getSide();
	void setHighest1vs1Rank(Int val);
	Int getHighest1vs1Rank();
	void setHighest2vs2Rank(Int val);
	Int getHighest2vs2Rank();
	Bool isMapSelected(const AsciiString &mapName);
	void setMapSelected(const AsciiString &mapName, Bool selected);
	// getLastLadderAddr 0x005DF4B9 and getLastLadderPort 0x005DF50A fold with CustomMatchPreferences' identical bodies: the map names them there (CustomMatchPreferences.h).

	Int getMaxDisconnects();
	Int getMaxPoints();
	Int getMinPoints();
	Int getWaitTime();
	Int getNumPlayers();
	Int getMaxPing();
	void setLastLadder(const AsciiString &addr, UnsignedShort port);
	void setMaxDisconnects(Int val);
	void setMaxPoints(Int val);
	void setMinPoints(Int val);
	void setWaitTime(Int val);
	void setNumPlayers(Int val);
	void setMaxPing(Int val);
};
// SIZE 0x14
typedef char QuickMatchPreferencesSize[(sizeof(QuickMatchPreferences) == 0x14) ? 1 : -1];

#endif
