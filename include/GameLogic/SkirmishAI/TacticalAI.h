#pragma once

#include "Common/Vector.h"

class AITactic;
class AITacticsGenerator;
class AITarget;
class AITargetChooser;
class Object;
class Player;
class Rva00506A52;
class Team;
class Xfer;
struct Rva002C6234InterestZone;

// The base constructor at 0x00506B1B builds the three-slot table 0x00C63F9C.
class Rva00506B1B
{
public:
    Rva00506B1B();
    virtual ~Rva00506B1B();
    virtual void rva002C6779() = 0;
    virtual void rva002C61AF() = 0;

protected:
    bool m_unk0x04; // set false by the base constructor
};

// Constructor 0x002C60E4 calls 0x00506B1B and stores the table 0x00C004E4.
class TacticalAI : public Rva00506B1B
{
public:
    TacticalAI(Player *player, bool createChooser);
    virtual ~TacticalAI();
    virtual void rva002C6779();
    virtual void rva002C61AF();

    void Register(Team *team);   // 0x002C5FAA
    void UnRegister(Team *team); // 0x002C5FB2
    void DoXfer(Xfer *xfer);
    void updateInterestZones();
    bool checkEnemyForAttackMove(Object *object, Object *enemy);

private:
    Player *m_player; // 0x002C6779 passes it to the generator when activating a tactic
    AITargetChooser *m_targetChooser; // constructor 0x0050542B at 0x002C6144
    AITacticsGenerator *m_tacticsGenerator; // 0x002C5FAA, 0x002C5FB2 and 0x002C63F6
    AITarget *m_selectedTarget; // 0x002C6779 stores the result of getBestTarget (0x005053A4)
    AITarget *m_unk0x18; // 0x002C6779 uses this target if no chooser is present
    Rva00506A52 *m_unk0x1C; // allocated at 0x002C617C, updated through 0x00506AFA
    _STL::vector<Rva002C6234InterestZone *> m_interestZones; // 0x002C63A1 saves and restores these records
};
