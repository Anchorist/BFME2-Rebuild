// W3DSailModelDrawModuleData.h: the INI data of W3DSailModelDraw. SIZE 0x194.
// Target facts: the constructor 0x000D0737 calls W3DModelDrawModuleData's constructor 0x000C8EEF, zeroes +0x188,
// loads +0x18C and +0x190 from constants, and stores the vtable 0x00BC6870 at +0x0; buildFieldParse 0x000D0774
// calls W3DModelDrawModuleData::buildFieldParse 0x000C9240, then adds the table of three entries (MaxRotationDegrees
// +0x188, BlowingThresholdDegrees +0x18C: angle reals; AboutDamping +0x190: a real).
#pragma once
#ifndef BFME2_W3DSAILMODELDRAWMODULEDATA_H
#define BFME2_W3DSAILMODELDRAWMODULEDATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/W3DModelDrawModuleData.h"

class MultiIniFieldParse;

typedef char W3DSailModelDrawModuleData_base_size[(sizeof(W3DModelDrawModuleData) == 0x188) ? 1 : -1];

class INI;
class W3DSailModelDrawModuleData : public W3DModelDrawModuleData
{
public:
	W3DSailModelDrawModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);

	Real m_maxRotationDegrees;                             // +0x188 MaxRotationDegrees; angle
	Real m_blowingThresholdDegrees;                        // +0x18C BlowingThresholdDegrees; angle
	Real m_aboutDamping;                                   // +0x190 AboutDamping
};
// SIZE 0x194
typedef char W3DSailModelDrawModuleData_size[(sizeof(W3DSailModelDrawModuleData) == 0x194) ? 1 : -1];
typedef char W3DSailModelDrawModuleData_off_m_maxRotationDegrees[(offsetof(W3DSailModelDrawModuleData, m_maxRotationDegrees) == 0x188) ? 1 : -1];
typedef char W3DSailModelDrawModuleData_off_m_blowingThresholdDegrees[(offsetof(W3DSailModelDrawModuleData, m_blowingThresholdDegrees) == 0x18C) ? 1 : -1];
typedef char W3DSailModelDrawModuleData_off_m_aboutDamping[(offsetof(W3DSailModelDrawModuleData, m_aboutDamping) == 0x190) ? 1 : -1];

#endif
