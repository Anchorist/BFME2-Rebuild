// War of the Ring army. Native constructor 0x0031A257 installs Snapshot at +0
// and LivingWorldTurnObserver at +4. The 0x98-byte allocation precedes the
// constructor call in 0x0031A953.
#pragma once

#include "Common/GameAudio.h"
#include "Common/Snapshot.h"
#include "GameLogic/LivingWorldTurnObserver.h"

class LivingWorldRegion;
class LivingWorldPlayer;

class LivingWorldArmy : public Snapshot, public LivingWorldTurnObserver
{
public:
	virtual ~LivingWorldArmy();						// deleting slot 0x0031A00E
	virtual void loadPostProcess();						// 0x0031A02A
	virtual const char *GetSnapshotName() const;				// 0x00319E76
	virtual void xfer(Xfer *xfer);						// 0x0031A6DB
	virtual void BeginTurn(Int, Int);					// observer slot 0; receiver +4, 0x003191E2

	void rva00318EC0();							// 0x00318EC0 updates owner colour
	void rva0031911F(Int ownerPlayerID);					// 0x0031911F stores the owner, then updates colour
	bool rva00318F42();							// 0x00318F42
	void stopSound();							// 0x00318BEB
	LivingWorldRegion *getRegion();						// 0x00318C32
	Int getRegionID();							// 0x00318C79
	bool isOwnedBy(const LivingWorldPlayer *player);				// 0x00318CEB
	bool isOwnedBy(Int playerID);						// 0x00318D05
	void rva00318C05(bool flag);						// 0x00318C05

	unsigned char m_unk0x08[0x20 - 0x08];					// +0x08 begins with the 0x330757 listener member
	Int m_id;								// +0x20, LivingWorldLogic::findCityArmy 0x002B3187
	unsigned char m_unk0x24[0x44 - 0x24];
	Real m_posX;								// +0x44, getRegion 0x00318C32
	Real m_posY;								// +0x48
	unsigned char m_unk0x4C[0x54 - 0x4C];
	Int m_ownerPlayerID;							// +0x54, isOwnedBy 0x00318CEB and setter 0x0031911F
	unsigned char m_unk0x58[0x60 - 0x58];
	AudioHandle m_soundHandle;						// +0x60, removed by stopSound 0x00318BEB
	unsigned char m_unk0x64[0x78 - 0x64];
	Int m_unk0x78;								// +0x78, passed to 0x0023D007 by removeArmy
	unsigned char m_unk0x7C[0x8C - 0x7C];
	LivingWorldRegion *m_region;						// +0x8C, cached by getRegion 0x00318C32
	unsigned char m_unk0x90[0x98 - 0x90];
};

typedef char LivingWorldArmySizeCheck[sizeof(LivingWorldArmy) == 0x98 ? 1 : -1];
