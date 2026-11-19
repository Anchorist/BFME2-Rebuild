// Portions derived from Command & Conquer Generals and Command & Conquer Generals Zero Hour, (c) Electronic Arts Inc., GPL-3.0-or-later; see LICENSE and NOTICE.
// RTS3DScene uses the WW3D scene at +0 and the subsystem at +0x108.
// The constructor 0x0006F470 installs tables 0x007C63C8 and 0x007C6390.
// The secondary deleting destructor 0x0006F796 adjusts this by -0x108.
// The allocation at 0x0046B38 is 0x818 bytes.
#pragma once

#include "Common/SubsystemInterface.h"
#include "WW3D2/LightEnvironmentClass.h"
#include "WW3D2/SceneClass.h"

class LightClass;
class MaterialPassClass;
class W3DDynamicLight;
class W3DShroudMaterialPassClass;

class RTS3DScene : public SimpleSceneClass, public SubsystemInterface
{
public:
	RTS3DScene();
	virtual ~RTS3DScene();

	virtual void Render(RenderInfoClass &rinfo);
	virtual void Customized_Render(RenderInfoClass &rinfo);
	virtual void Visibility_Check(CameraClass *camera);

	virtual void init();
	virtual void reset();
	virtual void update();
	virtual void draw();

	void doRender(CameraClass *camera);
	void Flush(RenderInfoClass &rinfo);
	W3DDynamicLight *getADynamicLight();

protected:
	void renderOneObject(RenderInfoClass &rinfo, RenderObjClass *robj, Int localPlayerIndex, Int flags);
	void updateFixedLightEnvironments(RenderInfoClass &rinfo);
	void flushOccludedObjectsIntoStencil(RenderInfoClass &rinfo);

	RefMultiListClass<RenderObjClass> m_dynamicLightList;			// +0x114
	Bool m_drawTerrainOnly;						// +0x12C
	LightClass *m_globalLight[LightEnvironmentClass::MAX_LIGHTS];	// +0x130
	LightClass *m_scratchLight;					// +0x140
	Vector3 m_infantryAmbient;					// +0x144
	LightClass *m_infantryLight[LightEnvironmentClass::MAX_LIGHTS];	// +0x150
	Int m_numGlobalLights;						// +0x160
	LightEnvironmentClass m_defaultLightEnv;				// +0x164
	LightEnvironmentClass m_foggedLightEnv;				// +0x38C
	LightEnvironmentClass m_infantryLightEnv;			// +0x5B4
	Bool m_useSceneLighting;						// +0x7DC, copied to each light environment
	W3DShroudMaterialPassClass *m_shroudMaterialPass;			// +0x7E0
	MaterialPassClass *m_maskMaterialPass;				// +0x7E4
	MaterialPassClass *m_occludedMaterialPass;			// +0x7E8
	Int m_customPassMode;						// +0x7EC, render dispatch reads values 0 through 7
	Int m_translucentObjectsCount;					// +0x7F0
	RenderObjClass **m_translucentObjectsBuffer;			// +0x7F4
	Int m_occludedObjectsCount;					// +0x7F8
	RenderObjClass **m_potentialOccluders;				// +0x7FC
	RenderObjClass **m_potentialOccludees;				// +0x800
	RenderObjClass **m_nonOccludersOrOccludees;			// +0x804
	Int m_numPotentialOccluders;					// +0x808
	Int m_numPotentialOccludees;					// +0x80C
	Int m_numNonOccluderOrOccludee;					// +0x810
	CameraClass *m_camera;						// +0x814
};

typedef char RTS3DSceneSize[(sizeof(RTS3DScene) == 0x818) ? 1 : -1];
