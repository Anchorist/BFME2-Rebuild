// The Apt screen that displays the NAT connection grid.
#pragma once
#ifndef BFME2_APTCONNECTIONSCREEN_H
#define BFME2_APTCONNECTIONSCREEN_H

#include "GameClient/AptCallbackHost.h"
#include "GameNetwork/PortNegotiationListener.h"

class PortNegotiationSchema;
class PortNegotiationPing;

class AptConnectionScreen : public AptCallbackHost, public PortNegotiationListener
{
public:
	AptConnectionScreen(void *level);						// 0x005DB6E2
	virtual ~AptConnectionScreen();							// 0x005DB681
	virtual void onNegotiationChanged(void *schema, int row, int column);
	virtual void onPairChanged(void *schema, int row, int column);

	void OnRetryConnections(const char *);					// 0x005DB36A: "Connection::OnRetryConnections", asks the NAT to retry its failed pairs
	static int GetPingImageEnum(PortNegotiationPing *ping);	// 0x005DB37C: the ping quality band (0 none .. 3 bad) of a measured pair
	void UpdateSlotName(int slot);							// 0x005DB3B3: shows the slot's player name and number
	void UpdateGrid(PortNegotiationSchema *schema, int row, int column);	// 0x005DB512: plays the cell's "UpdateConnection_<row>_<column>" state
	void rva005DB630();										// 0x005DB630: refreshes the eight slot names
	void RedrawGrid(const char *);							// 0x005DB647: "Connection::RedrawGrid"

	void *m_level;											// +0x5C
};
typedef char AptConnectionScreenSizeCheck[sizeof(AptConnectionScreen)==0x60 ? 1 : -1];

#endif
