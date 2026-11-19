#pragma once
#include "Common/ModelConditionFlags.h"
class ObjectCreationList;
class RiderInfo
{
public:
 RiderInfo();
 RiderInfo(const RiderInfo &);
 ModelConditionFlags m_conditions; // 0x00, update passes all 19 words to Object
 int m_animationTime; // 0x4C
 ObjectCreationList *m_creation; // 0x50
};
// SIZE 0x54
