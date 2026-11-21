#pragma once
#include "Common/Array.h"
#include "GameLogic/Module/ModuleData.h"
#include "GameLogic/Module/RiderInfoArray.h"
class INI;
class DetachableRiderUpdateModuleData : public ModuleData
{
public:
	DetachableRiderUpdateModuleData();
 static void buildFieldParse(MultiIniFieldParse &);
 static ModuleData *friend_newModuleData(INI *ini);
 RiderInfoArray m_records; // 0x08
 Array<AsciiString> m_names; // 0x14
 int m_weapon; // 0x20
 bool m_riderlessHordeFlees; // 0x24
 bool m_removeRiderlessFromHorde; // 0x25
};
// SIZE 0x28
