// cl: /O2 /Oy-
// psdk
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=O0003E360 name-evidence=L
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
#include <windows.h>
// FUNCTION: BFME2 0x0003E360 size=89 name=?DebugInternalAssert@@YAXPBDH0@Z evidence=N:ledger tier=B hypothesis:mm1-fragment-path-elsewhere
void DebugInternalAssert(const char *file, int line, const char *msg)
{
	char buf[512];
	wsprintfA(buf, "File %s, line %i:\n%s", file, line, msg);
	MessageBoxA(NULL, buf, "Internal assert failed", MB_OK | MB_ICONHAND | MB_TASKMODAL | MB_SETFOREGROUND);
	TerminateProcess(GetCurrentProcess(), 666);
}

// FUNCTION: BFME2 0x0003E3C0 size=19 name=?DebugFreeMemory@@YAXPAX@Z evidence=N:ledger tier=B hypothesis:mm1-fragment-path-elsewhere
void DebugFreeMemory(void *ptr)
{
	if (ptr)
		GlobalFree(ptr);
}
