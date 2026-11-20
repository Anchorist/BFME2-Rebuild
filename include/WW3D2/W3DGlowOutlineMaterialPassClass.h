// W3DGlowOutlineMaterialPassClass adds fading outline geometry to a material pass.
// 0x0073F85D constructs MaterialPassClass before the four outline members.
// GlowMaterial creates two 0x48-byte instances at 0x00362BFF and 0x00362C57.
#pragma once
#ifndef BFME2_W3D_GLOW_OUTLINE_MATERIAL_PASS_CLASS_H
#define BFME2_W3D_GLOW_OUTLINE_MATERIAL_PASS_CLASS_H

#include "WW3D2/MaterialPassClass.h"

class W3DGlowOutlineMaterialPassClass : public MaterialPassClass
{
public:
	W3DGlowOutlineMaterialPassClass(int color, float intensity);	// 0x0073F85D
	virtual ~W3DGlowOutlineMaterialPassClass();
	virtual void Install_Materials(void) const;
	virtual void UnInstall_Materials(void) const;

	int UpdateFadeState();
	void SetFadeState(int state) { m_fadeState = state; }

private:
	int m_color;			// +0x38 packed color
	float m_intensity;		// +0x3C constructor argument
	int m_fadeState;		// +0x40 stored by GlowMaterial
	float m_fadeFactor;		// +0x44 updated by UpdateFadeState
};

typedef char W3DGlowOutlineMaterialPassSize[(sizeof(W3DGlowOutlineMaterialPassClass) == 0x48) ? 1 : -1];

#endif
