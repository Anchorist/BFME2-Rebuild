#pragma once
#include "Common/GameType.h"
#include <vector>
#include <utility>
// Constructor 0x00567348 constructs the four STLport vectors at +0x04,
// +0x10, +0x1C and +0x2C. It copies the input vectors into the first two
// positions and stores the solver mode at +0x00. The solver at 0x005675B3
// uses +0x28 for the leftover count.
// Names and algorithm vocabulary originate in EA's GPLv3 Zero Hour source.
typedef std::pair<ObjectID,unsigned int> PairObjectIDAndUInt;
typedef std::pair<ObjectID,ObjectID> PairObjectID;
typedef std::vector<PairObjectIDAndUInt> EntriesVec;
typedef std::vector<PairObjectIDAndUInt> SpacesVec;
typedef std::vector<PairObjectID> SolutionVec;
enum SolutionType { PREFER_FAST_SOLUTION=0, PREFER_CORRECT_SOLUTION=0x7fffffff };
class PartitionSolver
{
protected:
    SolutionType m_howToSolve;
    EntriesVec m_data;
    SpacesVec m_spacesForData;
    SolutionVec m_currentSolution;
    unsigned int m_currentSolutionLeftovers;
    SolutionVec m_bestSolution;
public:
    PartitionSolver(const EntriesVec &entries, const SpacesVec &spaces, SolutionType mode);
    ~PartitionSolver();
    void solve();
    const SolutionVec &getSolution() const;
};

// Four 12-byte STLport vectors and two words.
typedef char PartitionSolverSize[(sizeof(PartitionSolver) == 0x38) ? 1 : -1];
