#pragma once

#include "Common/Vector.h"

class AITactic;
class AITarget;
class Player;
class Team;
class Xfer;

// The constructor at 0x00506909 builds eight consecutive vectors. The four
// setup functions populate the prototype vectors and 0x00505924 updates the
// neighboring active vectors.
class AITacticsGenerator
{
public:
    explicit AITacticsGenerator(Player *player);
    ~AITacticsGenerator();

    void Register(Team *team);
    void UnRegister(Team *team);
    void DoXfer(Xfer *xfer);
    bool activateTactic(AITarget *target, Player *player);

private:
    Player *m_player;
    _STL::vector<AITactic *> m_offensivePrototypes; // 0x00505E5D
    _STL::vector<AITactic *> m_offensiveTactics;
    _STL::vector<AITactic *> m_defensivePrototypes; // 0x00505F80
    _STL::vector<AITactic *> m_defensiveTactics;
    _STL::vector<AITactic *> m_expansionPrototypes; // 0x00505FD0
    _STL::vector<AITactic *> m_expansionTactics;
    _STL::vector<AITactic *> m_targetlessPrototypes; // 0x00506020
    _STL::vector<AITactic *> m_targetlessTactics;
};

// TacticalAI allocates 0x64 bytes at 0x002C6154 before calling the constructor.
typedef char AITacticsGeneratorSize[(sizeof(AITacticsGenerator) == 0x64) ? 1 : -1];
