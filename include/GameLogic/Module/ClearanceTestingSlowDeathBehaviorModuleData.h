// The geometry and terrain-height thresholds for the slow-death clearance check.
#pragma once
#ifndef BFME2_CLEARANCE_TESTING_SLOW_DEATH_BEHAVIOR_MODULE_DATA_H
#define BFME2_CLEARANCE_TESTING_SLOW_DEATH_BEHAVIOR_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/SlowDeathBehaviorModuleData.h"
#include "Common/Coord3D.h"
#include "Common/Geometry.h"

class INI;
class MultiIniFieldParse;

// Base SlowDeathBehaviorModuleData: the constructor calls its constructor on this. It ends at 0x190 (its own operator-new size);
// this class's members follow it.
typedef char ClearanceTestingSlowDeathBehaviorModuleData_base_size[(sizeof(SlowDeathBehaviorModuleData) == 0x190) ? 1 : -1];

class ClearanceTestingSlowDeathBehaviorModuleData : public SlowDeathBehaviorModuleData
{
public:
	ClearanceTestingSlowDeathBehaviorModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);

	// The partition test uses this geometry at the object-space offset below.
	GeometryInfo m_clearanceGeometry;
	Coord3D m_clearanceGeometryOffset;
	// The clearance test counts sample points above and below these relative heights.
	Real m_clearanceMaxHeight;
	Real m_clearanceMaxHeightFraction;
	Real m_clearanceMinHeight;
	Real m_clearanceMinHeightFraction;
};
// SIZE 0x208
typedef char ClearanceTestingSlowDeathBehaviorModuleData_size[(sizeof(ClearanceTestingSlowDeathBehaviorModuleData) == 0x208) ? 1 : -1];
typedef char ClearanceTestingSlowDeathBehaviorModuleData_off_m_clearanceGeometry[(offsetof(ClearanceTestingSlowDeathBehaviorModuleData, m_clearanceGeometry) == 0x190) ? 1 : -1];
typedef char ClearanceTestingSlowDeathBehaviorModuleData_off_m_clearanceGeometryOffset[(offsetof(ClearanceTestingSlowDeathBehaviorModuleData, m_clearanceGeometryOffset) == 0x1EC) ? 1 : -1];
typedef char ClearanceTestingSlowDeathBehaviorModuleData_off_m_clearanceMaxHeight[(offsetof(ClearanceTestingSlowDeathBehaviorModuleData, m_clearanceMaxHeight) == 0x1F8) ? 1 : -1];
typedef char ClearanceTestingSlowDeathBehaviorModuleData_off_m_clearanceMaxHeightFraction[(offsetof(ClearanceTestingSlowDeathBehaviorModuleData, m_clearanceMaxHeightFraction) == 0x1FC) ? 1 : -1];
typedef char ClearanceTestingSlowDeathBehaviorModuleData_off_m_clearanceMinHeight[(offsetof(ClearanceTestingSlowDeathBehaviorModuleData, m_clearanceMinHeight) == 0x200) ? 1 : -1];
typedef char ClearanceTestingSlowDeathBehaviorModuleData_off_m_clearanceMinHeightFraction[(offsetof(ClearanceTestingSlowDeathBehaviorModuleData, m_clearanceMinHeightFraction) == 0x204) ? 1 : -1];

#endif
