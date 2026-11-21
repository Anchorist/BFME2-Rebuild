#pragma once

#include "GameClient/DrawModule.h"

// The 0x000CEDE1 constructor installs table 0x007CD178 after DrawModule
// and clears its own byte at +0x0C. Its retail table has no other data witness.
class W3DBuffDraw : public DrawModule
{
public:
	W3DBuffDraw(Thing *thing, const ModuleData *moduleData);
	static Module *friend_newModuleInstance(Thing *thing, const ModuleData *moduleData);
	virtual NameKeyType getModuleNameKey() const;
	virtual void doDrawModule(const Matrix3D *) {}
	virtual void setShadowsEnabled(Bool) {}
	virtual void releaseShadows() {}
	virtual void allocateShadows() {}
	virtual void setFullyObscuredByShroud(Bool) {}
	virtual void reactToTransformChange(const Matrix3D *, const Coord3D *, Real) {}
	virtual void reactToGeometryChange() {}

protected:
	virtual void loadPostProcess() { DrawModule::loadPostProcess(); }
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

private:
	Bool m_drawFlag;
};

typedef char W3DBuffDraw_size[(sizeof(W3DBuffDraw) == 0x10) ? 1 : -1];

