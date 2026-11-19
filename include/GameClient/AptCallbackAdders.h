// Native callback registration owners used by AptCallbackHost.
#pragma once

#include "Apt/AptRef.h"
#include "Common/AsciiString.h"
#include "Common/Vector.h"

class AptCommandMap;
class AptCustomRender;
class AptExternHandler;
class AptOverButtonHandler;
class Image;

class AptCommandMapAdder
{
public:
	~AptCommandMapAdder();
	void AddCommandMap(const AsciiString &name, AptRef<AptCommandMap> callback);

private:
	_STL::vector<AsciiString> m_names;
};

class AptExternHandlerAdder
{
public:
	~AptExternHandlerAdder();
	void AddExternHandler(const AsciiString &name, int movieLevel, AptRef<AptExternHandler> callback);

private:
	_STL::vector<AsciiString> m_names;
};

class AptOverButtonHandlerAdder
{
public:
	~AptOverButtonHandlerAdder();
	void AddOverButtonHandler(const AsciiString &name, AptRef<AptOverButtonHandler> callback);

private:
	struct LevelHandler
	{
		int m_movieLevel;
		AsciiString m_name;
	};

	_STL::vector<AsciiString> m_names;
	_STL::vector<LevelHandler> m_levelHandlers;
};

class AptCustomRenderAdder
{
public:
	~AptCustomRenderAdder();
	void AddCustomRender(const AsciiString &name, AptRef<AptCustomRender> callback);

private:
	_STL::vector<AsciiString> m_names;
};

class AptCallbackAdders
{
public:
	~AptCallbackAdders();
	void rva00524725(const AsciiString &name, const Image *image);
	void rva00524767(const AsciiString &name, const AsciiString &asset);

private:
	_STL::vector<AsciiString> m_names;
};
