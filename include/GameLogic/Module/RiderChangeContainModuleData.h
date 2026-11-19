#pragma once

#include <stddef.h>
#include "Common/AsciiString.h"
#include "Common/GameType.h"
#include "GameLogic/Module/SiegeEngineContainModuleData.h"

enum WeaponSetType;
enum LocomotorSetType;

class RiderChangeContainModuleData : public SiegeEngineContainModuleData
{
public:
	RiderChangeContainModuleData();

	static void buildFieldParse(MultiIniFieldParse &parse);
	static void parseRiderInfo(INI *ini, void *instance, void *store, const void *userData);

	struct RiderSlot
	{
		RiderSlot();
		~RiderSlot();

		AsciiString m_riderTemplateName;
		WeaponSetType m_weaponSet;
		ModelConditionFlagType m_modelCondition;
		ObjectStatusTypes m_objectStatus;
		AsciiString m_commandSetOverride;
		LocomotorSetType m_locomotorSet;
	};

	enum { MAX_RIDERS = 8 };
	RiderSlot m_riders[MAX_RIDERS];			// Rider1 through Rider8.
	UnsignedInt m_scuttleDelay;
	ModelConditionFlagType m_scuttleStatus;
	Bool m_killRiderWhenVehicleDies;
};

typedef char RiderChangeContainModuleData_slot_size[(sizeof(RiderChangeContainModuleData::RiderSlot) == 0x18) ? 1 : -1];
typedef char RiderChangeContainModuleData_size[(sizeof(RiderChangeContainModuleData) == 0x284) ? 1 : -1];
typedef char RiderChangeContainModuleData_off_m_riders[(offsetof(RiderChangeContainModuleData, m_riders) == 0x1B8) ? 1 : -1];
typedef char RiderChangeContainModuleData_off_m_scuttleDelay[(offsetof(RiderChangeContainModuleData, m_scuttleDelay) == 0x278) ? 1 : -1];
typedef char RiderChangeContainModuleData_off_m_scuttleStatus[(offsetof(RiderChangeContainModuleData, m_scuttleStatus) == 0x27C) ? 1 : -1];
typedef char RiderChangeContainModuleData_off_m_killRiderWhenVehicleDies[(offsetof(RiderChangeContainModuleData, m_killRiderWhenVehicleDies) == 0x280) ? 1 : -1];
