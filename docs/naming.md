# What the placeholder names mean

The original program has no symbol names for most of its code, so a name is used only when there is evidence
for it (a string or export in `baseline/game.dat`, the class's own virtual table, or Zero Hour code that
corresponds). Everything else carries a placeholder that says what is known: its address.

| You will see | It means |
| --- | --- |
| `Rva00261513Filter`, `Rva004A2BF0` (a class) | A class whose real name is unknown, named after the address of one of its functions or of its virtual table in `baseline/game.dat`. |
| `rva0028C15E(...)` (a method or function) | A function whose real name is unknown, named after its address (RVA, relative to the image base `0x400000`). |
| `vfunc_0x58`, `slot27` | An entry of a class's virtual table whose real name is unknown: the byte offset (`0x58`) or the slot number (27) in that table. |
| `m_unk0x28`, `m_flag2C4` | A data member whose role is not known yet, named after its byte offset in the object. |
| `g_Va00E0333C` | A global variable named after its address (a VA, which is the RVA plus `0x400000`). |
| `src/unk/O0024EEBB.cpp` | A source file whose original name and place are not known yet, named after its first address. |
| `include/Draft/...` | A provisional class layout; only the Drafts that something includes matter (see the worklist). |

Replacing a placeholder with a real name, with the evidence in the pull request, is a contribution of its own.
