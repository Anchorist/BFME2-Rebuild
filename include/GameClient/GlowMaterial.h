// GlowMaterial holds a private outline pass and the shared pass for its color.
// The destructor at 0x00362CF2 restores the Snapshot vtable. The material
// constructor at 0x0036247C clears both pointers and the two saved words.
#pragma once
#ifndef BFME2_GLOW_MATERIAL_H
#define BFME2_GLOW_MATERIAL_H

#include "Common/GameType.h"
#include "Common/Snapshot.h"

class W3DGlowOutlineMaterialPassClass;

class GlowMaterial : public Snapshot
{
	friend class BuffInstance;

public:
	GlowMaterial();					// 0x0036247C
	virtual ~GlowMaterial();				// 0x00362CF2
	unsigned char IsActive();				// 0x00362499

protected:
	virtual void loadPostProcess();				// 0x003624FE
	virtual const char *GetSnapshotName() const;		// 0x00362493
	virtual void xfer(Xfer *xfer);				// 0x003624C4

private:
	W3DGlowOutlineMaterialPassClass *m_outline;		// +0x04
	W3DGlowOutlineMaterialPassClass *m_sharedOutline;	// +0x08
	UnsignedInt m_0C;					// +0x0C
	UnsignedInt m_fadeState;				// +0x10
};

typedef char GlowMaterialSize[(sizeof(GlowMaterial) == 0x14) ? 1 : -1];

#endif
