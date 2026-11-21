// DRAFT: DeflectSpecialPowerModuleData adds no fields of its own.
// Target facts: ModuleFactory allocates 0x18 bytes for it (the size of SpecialPowerUpdateModuleData), and its
// buildFieldParse 0x004C5442 calls SpecialPowerUpdateModuleData::buildFieldParse 0x005890ED and then adds an empty
// field table (one zero record), so the base is SpecialPowerUpdateModuleData and the table has no entries.
#pragma once
#include <stddef.h>
#include "GameLogic/Module/SpecialPowerUpdateModule.h"
class MultiIniFieldParse;
class DeflectSpecialPowerModuleData : public SpecialPowerUpdateModuleData {
public:
  static void buildFieldParse(MultiIniFieldParse &parse);
};
typedef char check_size_DeflectSpecialPowerModuleData[sizeof(DeflectSpecialPowerModuleData)==0x18?1:-1];
