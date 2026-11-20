// RayEffectSystem owns the GameClient's per-drawable ray records.
// Native constructor 0x002CEE96 constructs its SubsystemInterface, installs
// table 0x00802244 and constructs 128 0x1C-byte records at +0x0C.
#pragma once

#include "Common/Coord3D.h"
#include "Common/SubsystemInterface.h"

class Drawable;

struct RayEffectData
{
	const Drawable *draw;						// +0x00, matched by native 0x002CED59
	Coord3D startLoc;						// +0x04, copied by addRayEffect 0x002CED84
	Coord3D endLoc;							// +0x10, copied by addRayEffect 0x002CED84
};

class RayEffectSystem : public SubsystemInterface
{
public:
	RayEffectSystem();
	virtual ~RayEffectSystem();					// deleting slot 0x002CEEE6
	virtual void init();						// slot 1, 0x002CEE63
	virtual void reset() { init(); }					// slot 9, 0x005CB260 dispatches virtual slot 1
	virtual void update() {}						// slot 10, 0x000B3FD0 bare return

	void getRayEffectData(const Drawable *drawable, RayEffectData *out);
	void deleteRayEffect(const Drawable *drawable);
	void addRayEffect(const Drawable *drawable, const Coord3D *start, const Coord3D *end);

private:
	enum { MAX_RAY_EFFECTS = 128 };
	RayEffectData m_effectData[MAX_RAY_EFFECTS];				// +0x0C
};

typedef char RayEffectDataSizeCheck[sizeof(RayEffectData) == 0x1C ? 1 : -1];
