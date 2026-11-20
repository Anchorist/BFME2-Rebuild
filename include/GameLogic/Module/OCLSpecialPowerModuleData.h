// The object creation lists, placement policy and upgrade conditions for a special power.
#pragma once
#ifndef BFME2_O_C_L_SPECIAL_POWER_MODULE_DATA_H
#define BFME2_O_C_L_SPECIAL_POWER_MODULE_DATA_H

#include <stddef.h>
#include <vector>
#include "Common/GameType.h"
#include "Common/AsciiString.h"
#include "GameLogic/Module/SpecialPowerModuleData.h"
#include "GameLogic/ObjectFilter.h"

class INI;
class MultiIniFieldParse;
class ObjectCreationList;
enum ScienceType;

// One UpgradeOCL entry: the player's science that selects the list (OCLSpecialPower::findOCL 0x004C31A8 walks the vector in 8-byte steps).
struct OCLUpgradeEntry
{
	ScienceType m_science;							// +0x00
	const ObjectCreationList *m_ocl;				// +0x04
};

// Base SpecialPowerModuleData: the constructor calls its constructor on this. It ends at 0x7C (its own operator-new size);
// this class's members follow it.
typedef char OCLSpecialPowerModuleData_base_size[(sizeof(SpecialPowerModuleData) == 0x7C) ? 1 : -1];

// INI's CreateLocation name table uses this order. Some placement policies
// are specific to BFME II and are inserted among the older modes.
enum OCLCreateLocType
{
	CREATE_AT_EDGE_NEAR_SOURCE,
	CREATE_AT_EDGE_NEAR_TARGET,
	CREATE_AT_EDGE_NEAR_TARGET_AND_MOVE_TO_LOCATION,
	CREATE_AT_LOCATION,
	USE_OWNER_OBJECT,
	CREATE_ABOVE_LOCATION,
	CREATE_AT_EDGE_FARTHEST_FROM_TARGET,
	CREATE_CLOSEST_TO_SPAWN_POINT,
	USE_SECONDARY_OBJECT_LOCATION
};

class OCLSpecialPowerModuleData : public SpecialPowerModuleData
{
public:
	OCLSpecialPowerModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	virtual ~OCLSpecialPowerModuleData();
	static void parseUpgradeName(INI *ini, void *instance, void *store, const void *userData);	// 0x004C3859 (map: placeholder INI::Rva004C3859_ParseUpgradeName)

	_STL::vector<OCLUpgradeEntry> m_upgradeOCL;            // +0x7C UpgradeOCL (INI::Rva004C381C_ParseUpgradeOCL); findOCL 0x004C31A8 reads begin +0x7C, end +0x80
	const ObjectCreationList * m_ocl;                      // +0x88 OCL
	OCLCreateLocType m_createLocation;                     // CreateLocation
	_STL::vector<AsciiString> m_upgradeName;               // +0x90 UpgradeName (0x004C3859 pushes the next ascii token; ~OCLSpecialPowerModuleData 0x004C37C0 destroys it)
	ObjectFilter m_nearestSecondaryObjectFilter;           // +0x9C NearestSecondaryObjectFilter
};
// SIZE 0xA0
typedef char OCLSpecialPowerModuleData_size[(sizeof(OCLSpecialPowerModuleData) == 0xA0) ? 1 : -1];
typedef char OCLSpecialPowerModuleData_off_m_upgradeOCL[(offsetof(OCLSpecialPowerModuleData, m_upgradeOCL) == 0x7C) ? 1 : -1];
typedef char OCLSpecialPowerModuleData_off_m_ocl[(offsetof(OCLSpecialPowerModuleData, m_ocl) == 0x88) ? 1 : -1];
typedef char OCLSpecialPowerModuleData_off_m_createLocation[(offsetof(OCLSpecialPowerModuleData, m_createLocation) == 0x8C) ? 1 : -1];
typedef char OCLSpecialPowerModuleData_off_m_upgradeName[(offsetof(OCLSpecialPowerModuleData, m_upgradeName) == 0x90) ? 1 : -1];
typedef char OCLSpecialPowerModuleData_off_m_nearestSecondaryObjectFilter[(offsetof(OCLSpecialPowerModuleData, m_nearestSecondaryObjectFilter) == 0x9C) ? 1 : -1];

#endif
