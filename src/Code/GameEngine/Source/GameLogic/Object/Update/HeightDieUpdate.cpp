// cl: /O1
#include "Common/INI/FieldParse.h"
#include "Common/INI.h"
#include "Common/NameKeyGenerator.h"
#include "Common/Xfer.h"
#include "GameLogic/Module/HeightDieUpdate.h"
#include "GameLogic/Module/HeightDieUpdateModuleData.h"
// Tier B; object=O0048FBD3 evidence=Z flags=align=A
// Extent is a hypothesis; only Object VERIFIED establishes recovery.
// Edges: left=unknown-rows right=unknown-rows
// The height-die module and its INI data. The field table is the one retail
// passes to MultiIniFieldParse::add at 0x0048FCA1 (0x00C4CFC8), which names
// every member and its parser.
// FUNCTION: BFME2 0x0048FBBA size=25 name=??1HeightDieUpdate@@UAE@XZ evidence=N:ledger tier=B hypothesis:mm1-held-object-same-path
HeightDieUpdate::~HeightDieUpdate()
{
}

// FUNCTION: BFME2 0x0048FBD3 size=6 name=?GetSnapshotName@HeightDieUpdate@@MBEPBDXZ evidence=N:ledger

const char *HeightDieUpdate::GetSnapshotName(void) const
{
	return "HeightDieUpdate";
}

// FUNCTION: BFME2 0x0048FBD9 size=87 name=?xfer@HeightDieUpdate@@MAEXPAVXfer@@@Z evidence=N:ledger

void HeightDieUpdate::xfer(Xfer *xfer)
{
	UpdateModule::xfer(xfer);

	if (xfer->IsLightCRC())
		return;

	xfer->Version1();

	*xfer == m_triggeredHeightDeath;
	*xfer == m_destroyedAttachedParticles;
	*xfer == m_lastPosition;
	*xfer == m_firstCheckFrame;
}

// FUNCTION: BFME2 0x0048FC30 size=69 name=?getModuleNameKey@HeightDieUpdate@@UBE?AW4NameKeyType@@XZ evidence=N:ledger

NameKeyType HeightDieUpdate::getModuleNameKey(void) const
{
	static NameKeyType key = TheNameKeyGenerator->nameToKey("HeightDieUpdate");
	return key;
}

// FUNCTION: BFME2 0x0048FC75 size=44 name=??0HeightDieUpdateModuleData@@QAE@XZ evidence=N:ledger

HeightDieUpdateModuleData::HeightDieUpdateModuleData()
{
	m_targetHeight = 0.0f;
	m_targetHeightIncludesStructures = false;
	m_onlyWhenMovingDown = false;
	m_destroyAttachedParticlesAtHeight = -1.0f;
	m_snapToGroundOnDeath = false;
	m_initialDelay = 0;
}

// FUNCTION: BFME2 0x0048FCA1 size=17 name=?buildFieldParse@HeightDieUpdateModuleData@@SAXAAVMultiIniFieldParse@@@Z evidence=N:ledger

const FieldParse HeightDieUpdateModuleDataFieldParseTable[] =
{
	{ "TargetHeight", &INI::parseReal, NULL, offsetof(HeightDieUpdateModuleData, m_targetHeight) },
	{ "TargetHeightIncludesStructures", &INI::parseBool, NULL, offsetof(HeightDieUpdateModuleData, m_targetHeightIncludesStructures) },
	{ "OnlyWhenMovingDown", &INI::parseBool, NULL, offsetof(HeightDieUpdateModuleData, m_onlyWhenMovingDown) },
	{ "DestroyAttachedParticlesAtHeight", &INI::parseReal, NULL, offsetof(HeightDieUpdateModuleData, m_destroyAttachedParticlesAtHeight) },
	{ "SnapToGroundOnDeath", &INI::parseBool, NULL, offsetof(HeightDieUpdateModuleData, m_snapToGroundOnDeath) },
	{ "InitialDelay", &INI::parseDurationUnsignedInt, NULL, offsetof(HeightDieUpdateModuleData, m_initialDelay) },
	{ NULL, NULL, NULL, 0 }
};

void HeightDieUpdateModuleData::buildFieldParse(MultiIniFieldParse &p)
{
	p.add(HeightDieUpdateModuleDataFieldParseTable, 0);
}

// FUNCTION: BFME2 0x0048FCB2 size=77 name=??0HeightDieUpdate@@QAE@PAVThing@@PBVModuleData@@@Z evidence=N:ledger

HeightDieUpdate::HeightDieUpdate(Thing *thing, const ModuleData *moduleData) :
	UpdateModule(thing, moduleData)
{
	m_firstCheckFrame = 0xFFFFFFFF;
	m_triggeredHeightDeath = false;
	m_destroyedAttachedParticles = false;
	m_lastPosition.x = -1.0f;
	m_lastPosition.y = -1.0f;
	m_lastPosition.z = -1.0f;
}

// FUNCTION: BFME2 0x0048FD1B size=604 name=?update@HeightDieUpdate@@UAE?AW4UpdateSleepTime@@XZ evidence=N:ledger
