#pragma once
// SIZE 0x10. No base or virtual functions.
// Retail XferSaveAsText::operator== 0x0060DCE1 reads these typed fields in order;
// the transfer format strings label the components.

#include <stddef.h>
struct RGBAColorInt
{
    unsigned int red; // 0x0
    unsigned int green; // 0x4
    unsigned int blue; // 0x8
    unsigned int alpha; // 0xC
};
typedef char RGBAColorIntSize[(sizeof(RGBAColorInt) == 0x10) ? 1 : -1];
