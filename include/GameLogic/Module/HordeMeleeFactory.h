// Thing templates store one of these factories for the horde melee policy.
#pragma once

#include "Common/GameType.h"
#include "Common/ModelConditionFlags.h"

class HordeContain;
class HordeMeleeBase;
class MultiIniFieldParse;

class HordeMeleeFactory
{
public:
	virtual ~HordeMeleeFactory();
	virtual HordeMeleeBase *create(HordeContain *horde) = 0;
	virtual void buildFieldParse(MultiIniFieldParse &) {}
};

class HordeMeleeFormationConfig : public HordeMeleeFactory
{
public:
	HordeMeleeFormationConfig();
	virtual HordeMeleeBase *create(HordeContain *horde);
	virtual void buildFieldParse(MultiIniFieldParse &parse);

	Bool m_followLeader;
	Real m_distanceToActiveLeader;
	Real m_distanceToPassiveLeader;
};

class HordeMeleeAmoebaConfig : public HordeMeleeFactory
{
public:
	HordeMeleeAmoebaConfig();
	virtual HordeMeleeBase *create(HordeContain *horde);
	virtual void buildFieldParse(MultiIniFieldParse &parse);

	Real m_facingBonus;
	Real m_angleLimitCos;
	Real m_innerRange;
	Real m_outerRange;
	Real m_outerRangeBuildings;
	ModelConditionFlags m_idleModelConditions;
	UnsignedInt m_delayUntilIdle;
	UnsignedInt m_delayRandomActivateMin;
	UnsignedInt m_delayRandomActivateMax;
};

typedef char HordeMeleeFormationConfigSizeCheck[sizeof(HordeMeleeFormationConfig) == 0x10 ? 1 : -1];
typedef char HordeMeleeAmoebaConfigSizeCheck[sizeof(HordeMeleeAmoebaConfig) == 0x70 ? 1 : -1];
