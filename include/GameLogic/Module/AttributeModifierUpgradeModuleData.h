// The attribute modifier to apply when the upgrade takes effect.
#pragma once
#ifndef BFME2_ATTRIBUTE_MODIFIER_UPGRADE_MODULE_DATA_H
#define BFME2_ATTRIBUTE_MODIFIER_UPGRADE_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/UpgradeModule.h"
#include "Common/AsciiString.h"

class INI;
class MultiIniFieldParse;

class AttributeModifierUpgradeModuleData : public UpgradeModuleData
{
public:
	AttributeModifierUpgradeModuleData() throw();
	static void buildFieldParse(MultiIniFieldParse &parse);
	static ModuleData *friend_newModuleData(INI *ini);
	virtual Bool slot11() const { return true; }

	AsciiString m_attributeModifier;                       // +0x118 AttributeModifier
};
// SIZE 0x11C
typedef char AttributeModifierUpgradeModuleData_size[(sizeof(AttributeModifierUpgradeModuleData) == 0x11C) ? 1 : -1];
typedef char AttributeModifierUpgradeModuleData_off_m_attributeModifier[(offsetof(AttributeModifierUpgradeModuleData, m_attributeModifier) == 0x118) ? 1 : -1];

#endif
