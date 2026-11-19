// The weather subsystem owns the five parsed weather records beginning at +0x30.
// Constructor 0x00318588 installs SubsystemInterface at +0 and Snapshot at +0x0C.
// Its element constructor 0x00318329 clears the reference at +0 and the flag at +4.
// The destructor at 0x0010F149 releases the AudioEventInfoRef's counted pointee.
#pragma once
#ifndef BFME2_GLOBALWEATHERSYSTEM_H
#define BFME2_GLOBALWEATHERSYSTEM_H

#include "Common/AudioEventRef.h"
#include "Common/INI/FieldParse.h"
#include "Common/Snapshot.h"
#include "Common/SubsystemInterface.h"

struct WeatherData
{
	AudioEventInfoRef m_weatherSound;								// 0x00
	Bool m_hasLightning;								// 0x04

	static const FieldParse m_fieldParseTable[];
};

typedef char WeatherDataSize[(sizeof(WeatherData) == 8) ? 1 : -1];

class GlobalWeatherSystem : public SubsystemInterface, public Snapshot
{
public:
	GlobalWeatherSystem();
	virtual ~GlobalWeatherSystem();

	virtual void init() {}
	virtual void reset();
	virtual void update();

	static void parseWeatherData(INI *ini);

protected:
	virtual void loadPostProcess();
	virtual const char *GetSnapshotName() const;
	virtual void xfer(Xfer *xfer);

private:
	UnsignedByte m_unk0x10[0x20];
	WeatherData m_weather[5];						// 0x30
};

extern GlobalWeatherSystem *TheGlobalWeatherSystem;

#endif /* BFME2_GLOBALWEATHERSYSTEM_H */
