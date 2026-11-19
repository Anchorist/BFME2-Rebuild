// RegionAwardDispute owns the players that can settle a contested region.
// The constructor at 0x002B644A installs the four-slot Snapshot table at
// RVA 0x007FE280 and constructs the player vector at +0x08.
// GetResolvableBy at 0x004FBED6 dereferences a vector element and reads the
// player's ID at +0x14 and kind at +0x44.
#pragma once
#ifndef BFME2_REGION_AWARD_DISPUTE_H
#define BFME2_REGION_AWARD_DISPUTE_H

#include <stddef.h>
#include <vector>
#include "Common/GameType.h"
#include "Common/Snapshot.h"

class LivingWorldPlayer;

#pragma pack(push, 1)
class RegionAwardDispute : public Snapshot
{
public:
	RegionAwardDispute();
	virtual ~RegionAwardDispute();

	Int GetResolvableBy();

	Int m_regionID;
	std::vector<LivingWorldPlayer *> m_players;
	UnsignedInt m_disputeFlags;	// constructor 0x004FC002 adds flag 0x20
	Int m_unk0x18;
	Bool m_resolved;			// hasUnresolvedDisputeFor skips this record when true

protected:
	virtual void loadPostProcess();
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);
};
#pragma pack(pop)

typedef char RegionAwardDisputePlayerOffset[(offsetof(RegionAwardDispute, m_players) == 0x08) ? 1 : -1];
typedef char RegionAwardDisputeResolvedOffset[(offsetof(RegionAwardDispute, m_resolved) == 0x1C) ? 1 : -1];

#endif
