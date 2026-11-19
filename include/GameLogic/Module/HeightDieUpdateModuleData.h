// Height-triggered death, including particles, direction and initial delay.
#pragma once
#ifndef BFME2_HEIGHTDIEUPDATEMODULEDATA_H
#define BFME2_HEIGHTDIEUPDATEMODULEDATA_H

#include "GameLogic/Module/ModuleData.h"

class MultiIniFieldParse;

class HeightDieUpdateModuleData : public ModuleData
{
public:
	HeightDieUpdateModuleData();

	static void buildFieldParse(MultiIniFieldParse &p);

	Real m_targetHeight;				// +0x08
	Bool m_targetHeightIncludesStructures;		// +0x0C
	Bool m_onlyWhenMovingDown;			// +0x0D
	Real m_destroyAttachedParticlesAtHeight;		// +0x10
	Bool m_snapToGroundOnDeath;			// +0x14
	UnsignedInt m_initialDelay;			// +0x18
};

#endif
