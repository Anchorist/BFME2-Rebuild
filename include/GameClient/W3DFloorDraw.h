#pragma once

#include "GameClient/W3DPropDraw.h"

class ModelConditionFlags;

// W3DFloorDraw's constructor at 0x000CF10B calls W3DPropDraw, then installs
// the 0x007CD4E0 primary table and the one-slot 0x007CD4D8 table at +0x10.
class FloorDrawRecordMatchInterface
{
public:
	virtual void updateRecordMatch(const ModelConditionFlags *conditions, int oldRecord, int newRecord) = 0;
};

class W3DFloorDraw : public W3DPropDraw, public FloorDrawRecordMatchInterface
{
public:
	W3DFloorDraw(Thing *thing, const ModuleData *moduleData);
	virtual ~W3DFloorDraw();
	virtual NameKeyType getModuleNameKey() const;
	virtual void doDrawModule(const Matrix3D *transform);
	virtual void *vslot09() { return static_cast<FloorDrawRecordMatchInterface *>(this); }
	virtual void *vslot10() { return static_cast<FloorDrawRecordMatchInterface *>(this); }
	virtual void setHidden(Bool hidden);
	virtual void vslot18(Bool hidden);
	virtual void reactToTransformChange(const Matrix3D *oldTransform, const Coord3D *oldPosition, Real oldAngle);
	virtual void updateRecordMatch(const ModelConditionFlags *conditions, int oldRecord, int newRecord);

protected:
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

private:
	// These four bytes are initialized together by the constructor. The last
	// three independently suppress installing the floor in 0x000CF2CF.
	Bool m_floorAdded;
	Bool m_hidden;
	Bool m_hiddenByDrawState;
	Bool m_hiddenByRecordMatch;
};

typedef char W3DFloorDraw_size[(sizeof(W3DFloorDraw) == 0x18) ? 1 : -1];

