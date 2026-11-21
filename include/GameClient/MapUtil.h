// MapUtil.h: the map-list and start-position helpers (GameClient/MapUtil). Only the functions a
// written body calls are declared; signatures are the map's decorated names.
#pragma once
#ifndef BFME2_MAPUTIL_H
#define BFME2_MAPUTIL_H

#include "Common/GameType.h"
#include "Common/AsciiString.h"

class GameInfo;
class GameWindow;

void positionStartSpots(AsciiString mapName, GameWindow **buttonMapStartPositions, GameWindow *mapWindow, GameWindow *extra);
void positionStartSpots(GameInfo *myGame, GameWindow **buttonMapStartPositions, GameWindow *mapWindow, GameWindow *extra);

Bool Rva00300E42Check(GameInfo *game);										// map-transfer eligibility check

#endif
