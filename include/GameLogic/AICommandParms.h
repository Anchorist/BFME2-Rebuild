// AICommandParms.h: the argument block AICommandInterface's command wrappers fill and
// pass to aiDoCommand. SIZE 0xC0.
// Portions derived from Command & Conquer Generals and Command & Conquer Generals Zero Hour, (c) Electronic Arts Inc., GPL-3.0-or-later; see LICENSE and NOTICE. Target facts: the constructor 0x00351BD0 takes the
// command type and the command source, zeroes +0x14..+0x1C, +0x2C..+0x34, +0x38 and
// +0xB8/+0xBC, builds the vector at +0x20 and a 0x7C-byte sub-object at +0x3C. The
// wrappers aiTightenToPosition 0x0036EA74, aiMoveToAndEvacuate 0x0036EAE0 and the rest
// copy the Coord3D to +0x08 (three movs), store an extra Int at +0x34 and a Real at +0x38,
// and the implicit destructor frees the vector at +0x20. Command types: 2 tighten,
// 3 move-and-evacuate, 4 move-evacuate-and-exit, 0xC force-attack, 0xD attack-team,
// 0x14..0x16 resume/heal/repair, 0x19 harvest, 0x1A exit, 0x1E..0x1F guard, 0x21 guard-area,
// 0x23 attack-area, 0x35 follow-path-append, 0x4E move with a facing, 0x51 attack-move with
// a facing, 0x52 amphibious move.
#pragma once
#ifndef BFME2_AICOMMANDPARMS_H
#define BFME2_AICOMMANDPARMS_H

#include "Common/GameType.h"
#include "Common/Coord3D.h"
#include "Common/Vector.h"
#include "GameLogic/Damage.h"

class AICommandInterface;
class Object;
class Team;
class Waypoint;
class PolygonTrigger;

// The command numbers aiDoCommand 0x002673F6 switches on (BFME2's own numbering). Each enumerator is the number its
// same-named AICommandInterface function passes to the AICommandParms constructor (named in the trailing comment);
// numbers whose caller has only an address name stay plain values. The map names the constructor
// ??0AICommandParms@@QAE@W4AICommandType@@W4CommandSourceType@@@Z.
enum AICommandType
{
	AICMD_NO_COMMAND = -1,
	AICMD_MOVE_TO_POSITION = 0x00,	// aiMoveToPosition
	AICMD_TIGHTEN_TO_POSITION = 0x02,	// aiTightenToPosition
	AICMD_MOVE_TO_AND_EVACUATE = 0x03,	// aiMoveToAndEvacuate
	AICMD_MOVE_TO_AND_EVACUATE_AND_EXIT = 0x04,	// aiMoveToAndEvacuateAndExit
	AICMD_IDLE = 0x05,	// aiIdle
	AICMD_FOLLOW_WAYPOINT_PATH = 0x06,	// aiFollowWaypointPath
	AICMD_FOLLOW_WAYPOINT_PATH_AS_TEAM = 0x07,	// aiFollowWaypointPathAsTeam
	AICMD_FORCE_ATTACK_OBJECT = 0x0C,	// aiForceAttackObject
	AICMD_ATTACK_TEAM = 0x0D,	// aiAttackTeam
	AICMD_ATTACK_POSITION = 0x0E,	// aiAttackPosition
	AICMD_HUNT = 0x12,	// aiHunt
	AICMD_RESUME_CONSTRUCTION = 0x14,	// aiResumeConstruction
	AICMD_GET_HEALED = 0x15,	// aiGetHealed
	AICMD_GET_REPAIRED = 0x16,	// aiGetRepaired
	AICMD_DOCK = 0x18,	// aiDock
	AICMD_HARVEST = 0x19,	// aiHarvest
	AICMD_EXIT = 0x1A,	// aiExit
	AICMD_EVACUATE = 0x1B,	// aiEvacuate
	AICMD_GO_PRONE = 0x1D,	// aiGoProne
	AICMD_GUARD_POSITION = 0x1E,	// aiGuardPosition
	AICMD_GUARD_OBJECT = 0x1F,	// aiGuardObject
	AICMD_GUARD_AREA = 0x21,	// aiGuardArea
	AICMD_ATTACK_AREA = 0x23,	// aiAttackArea
	AICMD_FACE_OBJECT = 0x26,	// aiFaceObject
	AICMD_FACE_POSITION = 0x27,	// aiFacePosition
	AICMD_WANDER_IN_PLACE = 0x2C,	// aiWanderInPlace
	AICMD_FOLLOW_WAYPOINT_PATH_EXACT = 0x32,	// aiFollowWaypointPathExact
	AICMD_MOVE_AWAY_FROM_UNIT = 0x34,	// aiMoveAwayFromUnit
	AICMD_FOLLOW_PATH_APPEND = 0x35,	// aiFollowPathAppend
	AICMD_MOVE_TO_POSITION_EVEN_IF_SLEEPING = 0x36,	// aiMoveToPositionEvenIfSleeping
	AICMD_MOVE_TO_AND_DELETE = 0x38,	// aiMoveToAndDelete
	AICMD_ATTACK_LEVEL_POSITION = 0x40,	// aiAttackLevelPosition
	AICMD_MOVE_TO_AND_DIE = 0x41,	// aiMoveToAndDie
	AICMD_GUARD_AREA_FROM_POSITION = 0x44,	// aiGuardAreaFromPosition
	AICMD_MOVE_TO_POSITION_SA = 0x47,	// aiMoveToPositionSA
	AICMD_MOVE_TO_POSITION_AND_FACE_DIRECTION = 0x4E,	// aiMoveToPositionAndFaceDirection
	AICMD_ATTACK_MOVE_TO_POSITION_AND_FACE_DIRECTION = 0x51,	// aiAttackMoveToPositionAndFaceDirection
	AICMD_MOVE_TO_POSITION_AMPHIBIOUS = 0x52	// aiMoveToPositionAmphibious
};

struct AICommandParms
{
	// 0x00351BD0: a COMDAT (expected in AIStates.cpp; /O1 keeps it out of line at every caller): Zero Hour's
	// initializer list and body (m_pos.zero(), m_coords.clear() = the erase(begin, end) call 0x002A133B).
	AICommandParms(AICommandType type, CommandSourceType cmdSource)
		: m_type(type), m_cmdSource(cmdSource), m_object(NULL), m_unk0x18(0), m_team(NULL),
		  m_waypoint(NULL), m_area(NULL), m_extraInt(0), m_facing(0.0f), m_unk0xB8(0), m_unk0xBC(0)
	{
		m_pos.zero();
		m_unk0x20.clear();
	}

	Int m_type;										// +0x00, the command (AICommandType)
	CommandSourceType m_cmdSource;					// +0x04
	Coord3D m_pos;									// +0x08, the position argument
	Object *m_object;								// +0x14, the target object of the object commands
	Int m_unk0x18;									// +0x18
	const Team *m_team;								// +0x1C, the team of aiAttackTeam
	_STL::vector<ObjectID> m_unk0x20;				// +0x20, freed by the implicit destructor
	const Waypoint *m_waypoint;						// +0x2C, the path of the waypoint commands
	const PolygonTrigger *m_area;						// +0x30, the area of the area commands
	Int m_extraInt;									// +0x34, the Int argument of the attack-move wrapper
	Real m_facing;									// +0x38, the facing argument of the *AndFaceDirection wrappers
	DamageInfo m_damage;							// +0x3C, built by DamageInfo's constructor 0x00263895 inside the out-of-line AICommandParms constructor (the 0x7C-byte sub-object is a DamageInfo; AIStoredCommand keeps the same one at +0x40)
	Int m_unk0xB8;									// +0xB8
	Int m_unk0xBC;									// +0xBC
};
// SIZE 0xC0

#endif
