#pragma once

#include <stddef.h>
#include "Common/GameType.h"

struct DrawableWheelInfo
{
	Real m_frontLeftHeightOffset;
	Real m_frontRightHeightOffset;
	Real m_rearLeftHeightOffset;
	Real m_rearRightHeightOffset;
	Real m_wheelAngle;
	Int m_framesAirborneCounter;
	Int m_framesAirborne;
};

// Both physics transform paths allocate 0x58 bytes (0x27082E and 0x276D17).
// Native constructor 0x270098 and deleting destructor 0x272349 install the
// single-slot table at RVA 0x7FAD38.
class DrawableLocoInfo
{
public:
	DrawableLocoInfo();
	virtual ~DrawableLocoInfo();

	// 0x270817 integrates the pitch and roll rates and their recoil terms.
	Real m_pitch;                   // +0x04
	Real m_pitchRate;
	Real m_roll;
	Real m_rollRate;
	Real m_yaw;                     // +0x14, float transferred at 0x27A2BF
	Real m_accelerationPitch;
	Real m_accelerationPitchRate;   // +0x1C, recoil at 0x271108
	Real m_accelerationRoll;
	Real m_accelerationRollRate;    // +0x24, recoil at 0x271108
	Real m_overlapZVel;              // +0x28, 0x27BA64
	Real m_overlapZ;                 // +0x2C, 0x27BA73
	// The constructor's 1.0 and two randomized initial phases follow the
	// DrawableLocoInfo member order in the predecessor layout.
	Real m_wobble;                   // +0x30
	Real m_yawModulator;             // +0x34
	Real m_pitchModulator;           // +0x38
	DrawableWheelInfo m_wheelInfo;   // +0x3C, suspension and air time in 0x276CFB
};

typedef char DrawableWheelInfo_size[(sizeof(DrawableWheelInfo) == 0x1C) ? 1 : -1];
typedef char DrawableLocoInfo_size[(sizeof(DrawableLocoInfo) == 0x58) ? 1 : -1];
typedef char DrawableLocoInfo_pitch_rate_offset[(offsetof(DrawableLocoInfo, m_accelerationPitchRate) == 0x1C) ? 1 : -1];
typedef char DrawableLocoInfo_roll_rate_offset[(offsetof(DrawableLocoInfo, m_accelerationRollRate) == 0x24) ? 1 : -1];
typedef char DrawableLocoInfo_wheels_offset[(offsetof(DrawableLocoInfo, m_wheelInfo) == 0x3C) ? 1 : -1];
