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
	virtual ~AptConnectionScreen();
	virtual void onNegotiationChanged(void *schema, int row, int column);
	virtual void onPairChanged(void *schema, int row, int column);

	void OnRetryConnections(const char *);					// "Connection::OnRetryConnections", asks the NAT to retry its failed pairs
	static int GetPingImageEnum(PortNegotiationPing *ping);	// The ping quality band (0 none .. 3 bad) of a measured pair
	void UpdateSlotName(int slot);							// Shows the slot's player name and number
	void UpdateGrid(PortNegotiationSchema *schema, int row, int column);	// Plays the cell's "UpdateConnection_<row>_<column>" state
	void rva005DB630();										// Refreshes the eight slot names
	void RedrawGrid(const char *);							// "Connection::RedrawGrid"

	void *m_level;											// +0x5C
};
typedef char AptConnectionScreenSizeCheck[sizeof(AptConnectionScreen)==0x60 ? 1 : -1];

#endif
