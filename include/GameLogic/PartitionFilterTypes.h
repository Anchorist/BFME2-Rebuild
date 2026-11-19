#pragma once

#include "Common/Coord3D.h"
#include "Common/GameType.h"
#include "GameLogic/PartitionFilter.h"

class GeometryInfo;

// SalvageCrateCollide chains this stateless filter after the same-player
// filter. 0x00260E44 checks the object's experience level.
class Rva00260E44Filter : public PartitionFilter
{
public:
    virtual bool allow(Object *object);
};

// 0x0027C2C9 stores the reference position, geometry and angle. The allow
// method at 0x00261603 compares GeometryInfo::CollidesWith to the stored flag.
class Rva00261603Filter : public PartitionFilter
{
public:
    Rva00261603Filter(const Coord3D &position, const GeometryInfo &geometry,
        Real angle, Bool requireCollision);
    virtual bool allow(Object *object);

private:
    Coord3D m_position;
    const GeometryInfo *m_geometry;
    Real m_angle;
    Bool m_requireCollision;
};

// WanderAIUpdate constructs this stateless filter when choosing an obstacle.
// 0x00261C72 tests the candidate's template kind-of mask.
class Rva00261C72Filter : public PartitionFilter
{
public:
    virtual bool allow(Object *object);
};

typedef char Rva00260E44FilterSize[(sizeof(Rva00260E44Filter) == 0x08) ? 1 : -1];
typedef char Rva00261603FilterSize[(sizeof(Rva00261603Filter) == 0x20) ? 1 : -1];
typedef char Rva00261C72FilterSize[(sizeof(Rva00261C72Filter) == 0x08) ? 1 : -1];
