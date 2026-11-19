// DarknessSpecialPowerModuleData.h: the INI data of DarknessSpecialPower. SIZE 0x84.
// Target facts: ModuleFactory registers the module with operator new 0x84 and
// constructor RVA 0x004C4F63; buildFieldParse RVA 0x004C4D9E calls SpecialPowerModuleData::buildFieldParse, then adds VA 0x00C5D7BC at +0x0.
// Each field uses the type written by its retail INI parser.
#pragma once
#ifndef BFME2_DARKNESS_SPECIAL_POWER_MODULE_DATA_H
#define BFME2_DARKNESS_SPECIAL_POWER_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/SpecialPowerModuleData.h"

class MultiIniFieldParse;
class FXList;

typedef char DarknessSpecialPowerModuleData_base_size[(sizeof(SpecialPowerModuleData) == 0x7C) ? 1 : -1];

class DarknessSpecialPowerModuleData : public SpecialPowerModuleData
{
public:
	DarknessSpecialPowerModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);

	Real m_darknessRadius;                                 // +0x7C DarknessRadius
	const FXList *m_darknessFX;                           // +0x80 DarknessFX
};
// SIZE 0x84
typedef char DarknessSpecialPowerModuleData_size[(sizeof(DarknessSpecialPowerModuleData) == 0x84) ? 1 : -1];
typedef char DarknessSpecialPowerModuleData_off_m_darknessRadius[(offsetof(DarknessSpecialPowerModuleData, m_darknessRadius) == 0x7C) ? 1 : -1];
typedef char DarknessSpecialPowerModuleData_off_m_darknessFX[(offsetof(DarknessSpecialPowerModuleData, m_darknessFX) == 0x80) ? 1 : -1];

#endif
