#pragma once

#include "Common/StlList.h"
#include "GameClient/DrawModule.h"

class RadiusDecal;

// Table 0x007CE218. The constructor at 0x000D181D initializes the list
// at +0x0C. The destructor walks its nodes and destroys each RadiusDecal.
class W3DTornadoDraw : public DrawModule
{
public:
	W3DTornadoDraw(Thing *thing, const ModuleData *moduleData);
	static Module *friend_newModuleInstance(Thing *thing, const ModuleData *moduleData);
	virtual ~W3DTornadoDraw();
	virtual NameKeyType getModuleNameKey() const;
	virtual void onDrawableBoundToObject();
	virtual void doDrawModule(const Matrix3D *transform);
	virtual void setShadowsEnabled(Bool) {}
	virtual void releaseShadows() {}
	virtual void allocateShadows() {}
	virtual void setFullyObscuredByShroud(Bool) {}
	virtual void reactToTransformChange(const Matrix3D *oldTransform, const Coord3D *oldPosition, Real oldAngle);
	virtual void reactToGeometryChange() {}

protected:
	virtual void loadPostProcess() { DrawModule::loadPostProcess(); }
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

private:
	void clearDecals();

	_STL::list<RadiusDecal *> m_decals;
};


// The factory at 0x00065139 allocates 0x10 bytes for this class.
typedef char W3DTornadoDraw_size[(sizeof(W3DTornadoDraw) == 0x10) ? 1 : -1];
