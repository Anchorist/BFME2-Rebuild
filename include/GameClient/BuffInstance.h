#pragma once

#include "Common/GameType.h"
#include "Common/RGBColor.h"
#include "Common/Snapshot.h"
#include "GameClient/GlowMaterial.h"

class Drawable;
class TBuff;
class ThingTemplate;

// Table 0x00817068 has the four Snapshot slots. The destructor at
// 0x00362D6C restores Snapshot's table after releasing the buff state.
class BuffInstance : public Snapshot
{
	friend class BuffManager;
public:
	BuffInstance();											// 0x00362D25
	virtual ~BuffInstance();
	void TurnOff(bool immediate);
	void Update(unsigned int frame);
	bool MakeNormalBuff(int type, int subType, const ThingTemplate *thingTemplate, Drawable *drawable, int duration);
	bool MakeGlowOutlineBuff(int type, int subType, Drawable *drawable, int duration, int color, float intensity);	// (unsupported: asserts)

protected:
	virtual void loadPostProcess() {}						// slot 1; the shared empty body 0x000B3FD0
	virtual const char *GetSnapshotName() const;			// (slot 2)
	virtual void xfer(Xfer *xfer);						// 0x003628D3 (slot 3)

public:
	bool m_active;											// +0x04
	Int m_type;												// +0x08
	Int m_subType;											// +0x0C
	Int m_duration;											// +0x10
	UnsignedInt m_frameLimit;								// +0x14 (compared unsigned in Update 0x003627B8)
	TBuff *m_glow;									// +0x18
	const ThingTemplate *m_thing;							// +0x1C
	RGBColor m_color;										// +0x20 (DoXfer transfers it as an RGBColor)
	Real m_intensity;										// +0x2C
	GlowMaterial m_material;								// +0x30
};
// SIZE 0x44
typedef char BuffInstance_size[(sizeof(BuffInstance) == 0x44) ? 1 : -1];
