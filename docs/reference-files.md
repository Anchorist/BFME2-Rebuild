# Write it like these

Five files show what a finished file looks like. In each, every function the file owns is credited MATCH with
its references proven, the file has its real name and path, it includes only real headers, and it has no
casts, stand-in types or placeholder names. They are different kinds of code on purpose. (The generated lines
at the top of a file, such as `// Tier ...` or `// Membership ...`, come from the maintainers' generator and are
being reduced; ignore them.)

1. **A plain class:** [`src/Code/GameEngine/Source/GameNetwork/FrameDataManager.cpp`](../src/Code/GameEngine/Source/GameNetwork/FrameDataManager.cpp).
   Sixteen functions that read like the network code they are: an array of frames sized by the two named
   globals, loops with ordinary indices, and members with role names (`m_frameData`, `m_quitFrame`,
   `m_isQuitting`). The one comment says where the two sizes come from. Nothing in it needs the disassembly to
   be understood.
2. **A data class and its owner:** [`src/Code/GameEngine/Source/GameNetwork/FrameData.cpp`](../src/Code/GameEngine/Source/GameNetwork/FrameData.cpp).
   One frame's command list, created on first use and reset in place, with an explicit initial state in the
   constructor. Ownership is visible: the destructor deletes what `init` created. It shows how a small class
   stays small.
3. **Library code in the library's own style:** [`src/Code/Libraries/Source/WWVegas/WWLib/hash.cpp`](../src/Code/Libraries/Source/WWVegas/WWLib/hash.cpp).
   The engine's chained hash table written with WWLib's own names (`HashTableClass`, `Reset`, `Advance_Next`)
   and its conventions, not modernised. The header comment states the hashing rule and why the table is freed
   with scalar `operator delete`. Keep a library's spelling and layout when you write its functions.
4. **A layout explained by evidence:** [`src/Code/Libraries/Source/WWVegas/WWMath/cullsys.cpp`](../src/Code/Libraries/Source/WWVegas/WWMath/cullsys.cpp).
   A base class and its system, where one comment gives the evidence for each member's place and role, and the
   code then uses those members by name. Null checks are written the way the original tests them.
5. **A class with virtual functions:** [`src/Code/GameEngine/Source/GameClient/DisplayString.cpp`](../src/Code/GameEngine/Source/GameClient/DisplayString.cpp)
   and its header `include/GameClient/DisplayString.h`. The header declares the virtual interface; the source
   defines the out-of-line members, and each text change goes through the virtual `notifyTextChanged()` so
   derived strings can react. It is short because the class is: no padding, no helpers the original lacks.

**Not yet:** no file that parses INI data qualifies. The nearest, `SupplyCenterDockUpdate.cpp`, still gives its
field-parse table literal offsets instead of member offsets and calls one function by a placeholder name.
Fixing that makes a good contribution and a sixth reference.

## Compare your file against this list

- Every function the file owns matches and its references are proven (the check's report says so).
- The file is at its real path, not `src/unk/`, and includes no header under `include/Draft/`.
- Types are the real ones: no `void *` or integer standing in for a known type, no caller casting a value back.
- Members and locals have role names, or an honest offset name where the role is not known.
- Names come from evidence for that class: a string or export in `baseline/game.dat`, the class's own virtual
  table, or Zero Hour code that corresponds.
- Library code keeps the library's names and style.
- Comments say why (evidence for a layout, an ownership rule, an intent). An address in a comment is acceptable
  only as evidence a reader can check, never to repeat the file's own function addresses.
- No dead code, no statements kept only to steer the compiler, no `__asm`, emitted bytes or pragmas.
- The `// FUNCTION:` and `// cl:` lines are unchanged.
- A maintainer can follow it without the disassembly.
