// cl: /O2 /G6 /Oy-
// psdk
#include <windows.h>
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G0003E3E0 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x0003E3E0 size=108 name=?DebugIsDebuggerAttached@@YA_NXZ evidence=N:ledger tier=B hypothesis:mm1-gap-unit
bool DebugIsDebuggerAttached()
{
	bool attached = false;
	HMODULE hKernel32 = LoadLibraryA("kernel32");
	if (hKernel32)
	{
		typedef BOOL (WINAPI *IsDebuggerPresentFn)(void);
		IsDebuggerPresentFn pIsDebuggerPresent = (IsDebuggerPresentFn)GetProcAddress(hKernel32, "IsDebuggerPresent");
		if (pIsDebuggerPresent)
			attached = pIsDebuggerPresent() != 0;
		typedef BOOL (WINAPI *CheckRemoteDebuggerPresentFn)(HANDLE, PBOOL);
		CheckRemoteDebuggerPresentFn pCheckRemote = (CheckRemoteDebuggerPresentFn)GetProcAddress(hKernel32, "CheckRemoteDebuggerPresent");
		BOOL remote = FALSE;
		if (pCheckRemote && pCheckRemote(GetCurrentProcess(), &remote))
			attached |= (remote != 0);
	}
	return attached;
}
