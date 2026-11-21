#pragma once

#include "GameClient/DrawModule.h"

class W3DDynamicLight;

// The 0x000CF91D constructor calls DrawModule and installs table 0x007CD728.
// The draw body 0x000CFC0C advances phase, interpolates the random height
// offset using the three floats at +0x14..0x1C, and writes light height.
class W3DLightDraw : public DrawModule
{
public:
	W3DLightDraw(Thing *thing, const ModuleData *moduleData);
	static Module *friend_newModuleInstance(Thing *thing, const ModuleData *moduleData);
	virtual ~W3DLightDraw();
	virtual NameKeyType getModuleNameKey() const;
	virtual void doDrawModule(const Matrix3D *transform);
	virtual void setShadowsEnabled(Bool) {}
	virtual void releaseShadows() {}
	virtual void allocateShadows() {}
	virtual void setHidden(Bool hidden);
	virtual void setFullyObscuredByShroud(Bool) {}
	virtual void reactToTransformChange(const Matrix3D *oldTransform, const Coord3D *oldPosition, Real oldAngle);
	virtual void reactToGeometryChange() {}

protected:
	virtual void loadPostProcess() { DrawModule::loadPostProcess(); }
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

private:
	W3DDynamicLight *m_light;
	Real m_phase;
	Real m_heightFramesRemaining;
	Real m_heightChangePerFrame;
	Real m_heightOffset;
};

typedef char W3DLightDraw_size[(sizeof(W3DLightDraw) == 0x20) ? 1 : -1];

