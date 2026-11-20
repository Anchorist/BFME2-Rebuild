#pragma once

#include "Common/GameType.h"
#include "Common/Snapshot.h"
#include "Common/SubsystemInterface.h"

class GateOpenBehaviorList;
class Object;
class Player;
class Team;
class TeamPrototype;

// FoundationAIUpdate passes ownership changes to the affected players' AI records.
class Rva002A8AB1Record
{
public:
    void rva002C6A3D(Object *object);
    void rva002C6A4E(Object *object);
    void rva002C6A76(Team *team);
    void rva004EC072(TeamPrototype *team);
    void rva004EC07D(TeamPrototype *team);
    void rva004EC2D4(ObjectID objectID); // Dozer completion calls this on the returned record
    void onUnitCreated(Object *factory, Object *unit);
};

struct Rva002A8F24Record
{
    // ScoreKeeper::updateFrame (0x0039D1F1) adds this field to the
    // player's frame money after following the +0x0C pointer.
    struct ScoreMoneySource
    {
        unsigned char m_unk0x00[0x14];
        int m_moneyForScore;
    };

    unsigned char m_unk0x00[0xC];
    ScoreMoneySource *m_scoreMoneySource;
};

// Construction puts SubsystemInterface first and Snapshot at +0xC.
// GetSnapshotName returns the subsystem's class name.
class SkirmishAIManager : public SubsystemInterface, public Snapshot
{
public:
    SkirmishAIManager();
    virtual ~SkirmishAIManager();

    virtual void init() {}
    virtual void reset();
    virtual void update();

    void UnRegister(Object *object);
    void rva002A9365(Object *object);
    Rva002A8F24Record *rva002A8F24(Player *player);
    Rva002A8AB1Record *rva002A8AB1(Player *player);

    unsigned char m_unk0x010[0x840];
    float m_aiRevivalCostDiscountLimit;
    float m_aiRevivalTimeDiscountLimit;
    unsigned char m_unk0x858[0x8];
    // Player::setPlayerType also creates AI for non-computer skirmish players when set.
    bool m_forceSkirmishPlayerAI;
    unsigned char m_unk0x861[0xDF];
    // Created by the manager and used by GateOpenAndCloseBehavior.
    GateOpenBehaviorList *m_gateList;

protected:
    virtual void loadPostProcess() {}
    virtual const char *GetSnapshotName() const;
    virtual void xfer(Xfer *xfer);
};

// GameEngine allocates this exact size before calling the constructor.
typedef char SkirmishAIManagerSizeCheck[sizeof(SkirmishAIManager) == 0x944 ? 1 : -1];

extern SkirmishAIManager *TheSkirmishAIManager;
