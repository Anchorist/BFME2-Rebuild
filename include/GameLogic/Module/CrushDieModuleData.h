// Crushing sounds and their play chances by impact type.
#pragma once
#ifndef BFME2_CRUSH_DIE_MODULE_DATA_H
#define BFME2_CRUSH_DIE_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/DestroyDieModuleData.h"
#include "Common/OpaqueRefElement4.h"

class INI;
class MultiIniFieldParse;

// Base DestroyDieModuleData: the constructor calls its constructor on this. It ends at 0x38 (its own operator-new size);
// this class's members follow it.
typedef char CrushDieModuleData_base_size[(sizeof(DestroyDieModuleData) == 0x38) ? 1 : -1];

class CrushDieModuleData : public DestroyDieModuleData
{
public:
	CrushDieModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);

	// CrushDie::onDie 0x00486327 indexes both arrays by CrushEnum (total, back end, front end) and reads the
	// handle's pointer (`cmp [data+0x38+4*type],0`) before building the sound; the table's tokens are
	// TotalCrushSound +0x38, BackEndCrushSound +0x3C, FrontEndCrushSound +0x40 (INI::parseAudioEventRTS 0x00339900).
	// The fourth slot is initialized with the other three and has no INI field.
	OpaqueRefElement4 m_crushSounds[4];                    // +0x38
	// TotalCrushSoundPercent +0x48, BackEndCrushSoundPercent +0x4C, FrontEndCrushSoundPercent +0x50.
	Int m_crushSoundPercent[4];                            // +0x48
};
// SIZE 0x58
typedef char CrushDieModuleData_size[(sizeof(CrushDieModuleData) == 0x58) ? 1 : -1];
typedef char CrushDieModuleData_off_m_crushSounds[(offsetof(CrushDieModuleData, m_crushSounds) == 0x38) ? 1 : -1];
typedef char CrushDieModuleData_off_m_crushSoundPercent[(offsetof(CrushDieModuleData, m_crushSoundPercent) == 0x48) ? 1 : -1];

#endif
