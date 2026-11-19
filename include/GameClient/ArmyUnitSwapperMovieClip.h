#pragma once

#include "Common/UnicodeString.h"
#include "GameClient/AptCallbackAdders.h"

namespace StrategicHUD
{
class ArmyUnitSwapperPanelFactory;
class ArmyUnitSwapperPanel;

// 0x5FDE24 installs the six-slot owner table at RVA 0x87A2E8
// and allocates a separate 0x50-byte Impl.
class ArmyUnitSwapperMovieClip
{
public:
	class Impl;
	typedef AptRef<ArmyUnitSwapperPanelFactory> PanelFactoryRef;

	ArmyUnitSwapperMovieClip(int level, const AsciiString &name,
	                        const PanelFactoryRef &top, const PanelFactoryRef &bottom);
	virtual ~ArmyUnitSwapperMovieClip();
	virtual void notifyClosed();
	virtual void notifyExit();
	virtual void notifyMoveDown();
	virtual void notifyMoveUp();
	virtual void notifySwap();

private:
	Impl *m_impl;
};

class ArmyUnitSwapperMovieClip::Impl
{
public:
	Impl(ArmyUnitSwapperMovieClip *owner, int level, const AsciiString &name,
	     const PanelFactoryRef &top, const PanelFactoryRef &bottom);
	~Impl();

	void OnOpen(const char *path);
	void OnClosed(const char *path);
	void OnExitButtonClicked(const char *path);
	void OnMoveDownButtonClicked(const char *path);
	void OnMoveUpButtonClicked(const char *path);
	void OnSwapButtonClicked(const char *path);
	void OnTopPanelLoaded(const char *path);
	void OnBottomPanelLoaded(const char *path);
	void OnPanelLoaded(int panel, const char *path);

private:
	struct PanelSlot
	{
		PanelSlot();
		~PanelSlot();

		// OnPanelLoaded constructs the panel from the factory and then
		// releases the factory. 0x5F4AD7 releases the panel through its
		// virtual AptRefTarget base.
		PanelFactoryRef m_panelFactory;
		AptRef<ArmyUnitSwapperPanel> m_panel;
		UnicodeString m_regionName;
		UnicodeString m_armyName;
		int m_unk0x10;
		int m_unk0x14;
	};

	ArmyUnitSwapperMovieClip *m_owner; // +0x00
	int m_level;                      // +0x04
	AsciiString m_name;               // +0x08
	AptCommandMapAdder m_commands;    // +0x0C
	int m_state;                      // +0x18, open and close callback state
	PanelSlot m_slots[2];              // +0x1C, 0x18-byte stride at 0x5FD80A
	bool m_unk0x4C;
	bool m_unk0x4D;
	bool m_unk0x4E;
};

typedef char ArmyUnitSwapperMovieClip_size[(sizeof(ArmyUnitSwapperMovieClip) == 8) ? 1 : -1];
typedef char ArmyUnitSwapperMovieClip_Impl_size[(sizeof(ArmyUnitSwapperMovieClip::Impl) == 0x50) ? 1 : -1];
}
