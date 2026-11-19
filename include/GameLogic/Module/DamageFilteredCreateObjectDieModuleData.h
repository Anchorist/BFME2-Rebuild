// Selects the creation list and its two damage subtype triggers.
#pragma once
#ifndef BFME2_DAMAGE_FILTERED_CREATE_OBJECT_DIE_MODULE_DATA_H
#define BFME2_DAMAGE_FILTERED_CREATE_OBJECT_DIE_MODULE_DATA_H

#include <stddef.h>
#include "Common/GameType.h"
#include "GameLogic/Module/DestroyDieModuleData.h"

class INI;
class MultiIniFieldParse;
class ObjectCreationList;

// Base DestroyDieModuleData: the constructor calls its constructor on this. It ends at 0x38 (its own operator-new size);
// this class's members follow it.
typedef char DamageFilteredCreateObjectDieModuleData_base_size[(sizeof(DestroyDieModuleData) == 0x38) ? 1 : -1];

class DamageFilteredCreateObjectDieModuleData : public DestroyDieModuleData
{
public:
	DamageFilteredCreateObjectDieModuleData();
	static void buildFieldParse(MultiIniFieldParse &parse);

	const ObjectCreationList *m_creationList;             // +0x38 CreationList
	Int m_damageTypeTriggersInstantly;                     // +0x3C DamageTypeTriggersInstantly; TheDamageSubTypeNames index, or the no-trigger default
	Int m_damageTypeTriggersForDuration;                   // +0x40 DamageTypeTriggersForDuration; TheDamageSubTypeNames index, or the no-trigger default
	UnsignedInt m_postFilterTriggeredDuration;             // +0x44 PostFilterTriggeredDuration; duration, frames
};
// SIZE 0x48
typedef char DamageFilteredCreateObjectDieModuleData_size[(sizeof(DamageFilteredCreateObjectDieModuleData) == 0x48) ? 1 : -1];
typedef char DamageFilteredCreateObjectDieModuleData_off_m_creationList[(offsetof(DamageFilteredCreateObjectDieModuleData, m_creationList) == 0x38) ? 1 : -1];
typedef char DamageFilteredCreateObjectDieModuleData_off_m_damageTypeTriggersInstantly[(offsetof(DamageFilteredCreateObjectDieModuleData, m_damageTypeTriggersInstantly) == 0x3C) ? 1 : -1];
typedef char DamageFilteredCreateObjectDieModuleData_off_m_damageTypeTriggersForDuration[(offsetof(DamageFilteredCreateObjectDieModuleData, m_damageTypeTriggersForDuration) == 0x40) ? 1 : -1];
typedef char DamageFilteredCreateObjectDieModuleData_off_m_postFilterTriggeredDuration[(offsetof(DamageFilteredCreateObjectDieModuleData, m_postFilterTriggeredDuration) == 0x44) ? 1 : -1];

#endif
