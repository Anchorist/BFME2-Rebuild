# Header layout witness (H5)

A header change that moves a member or a virtual slot is accepted only when a newly matched function shows it uses
that member. `h5_witness.py` produces that evidence. It runs inside the compiler check on its isolated compiler. It reads
headers and compiler objects; it never runs project code.

## How it proves a use

For one changed member of one class, the function's own source file is compiled twice:

- **control:** the member stays where it is, and a member of the same type with a probe name is added at the end.
- **moved:** the member's slot gets the probe name, and the member itself is declared at the end.

Both compiles have the same layout; each emits the class size and alignment as constants, and those must agree.
The only difference is which name sits in the original slot.

A use is recorded only when all of these hold:

- the function is newly matched with proof, and its head object is the authenticated one;
- in the control compile, the function is identical to the head object's (so code that depends on the class size is
  held, not counted);
- between control and moved, the function changes, with the same length and relocations;
- every changed byte is an operand whose control value lies inside the member's offset span, shifted by one amount
  everywhere.

Anything else is held with its reason. It never fails the rule. The operation is reported as `access`; it does not
claim read or write.

A virtual method works the same way, with a declared-only virtual method as the probe.

## What it cannot decide

These are held, with the reason in the run summary:

- a change of size or of a base class;
- bit-fields;
- several names in one declaration;
- members made by macros;
- members declared differently under `#if`;
- nested classes, templates and unions.

## Layout atoms (`h5_layout.py`)

The witness needs to know which members moved. `h5_layout.py` measures one class on each side of the change with the
same compiler and no debug information:

- a probe file includes the header and emits the class size, its alignment, and the offset and width of every plain
  data member as constants;
- the header gets one `friend` line at the top of the class body so the probe can name private members. A friend
  declaration does not change layout.

Comparing the two sides gives:

- **compatible shape, no atom:** members renamed, split or merged over exactly the same bytes, with the same size and
  alignment, and comment-only edits;
- **member atom:** a member whose offset or width changed, or a new member. Each needs a witness.
- **size, slot or base atom:** size or alignment changed, virtual functions changed, or base classes changed. These
  are held for now.
- **held:** a changed statement that could change layout but cannot be read, such as a macro call that is not a
  method, a bit-field or several names in one declaration. A removed member whose bytes are not taken over is also
  held: that belongs to the declaration rules.

## One header's H5 evidence (`h5_evidence.py`)

`evidence()` ties the two together for one changed header:

- it measures each class whose text changed (at most 4), on both sides;
- it witnesses each moved member (at most 4) against the newly matched functions;
- it returns `{layout, access, held}` for the layout join.

The compiler is passed in, so the same code runs on the compiler worker and in the tests.

`h5_bridge.py` runs `evidence()` inside the narrow comparison. It is meant to be called behind an export switch, like
the inline export, because that is where the head objects, the head compile rows and the compiler are available.

- It picks the rows newly matched with proof.
- It compiles the probes and the two header variants through the same sealed compiler request, with the header's
  bytes substituted in the source projection.
- It writes `header-h5.json`.

Nothing calls it yet.

## Declaration inventory for H4 (`h4_declarations.py`)

H4 needs a complete list of the declarations in each changed header, before and after. The compiler preprocesses a
probe that includes the header (`-E`, same include paths and defines). Its output keeps the original line numbers,
expands macros and drops inactive `#if` branches. `own_text()` rebuilds the header's own lines from it. The lexical
inventory of `tools/gates` then reads them, so a member made by a macro is listed and one in a dead branch is not.

- A layout assertion (`typedef char X[(offsetof(...) == N) ? 1 : -1]`) is read from the raw line.
- Anything else left unreadable makes the inventory incomplete, and H4 then holds.

The compiler worker does not have a preprocess-only mode yet. This module is the reading side only.

## Output

One record per witnessed use, in the form the layout join reads:

- `header`, `qualified_class`, `kind`, `identity` and `receiver_type`;
- `observed` (the member's new offset, width and type, from the layout probe);
- `operation: "access"`;
- the function's `rva`, `path` and `head_object`;
- `witness`: the function's decorated name and both object digests.

## Tests

`python3 -m unittest discover -s ci/header-witness/tests -v`. The fixture holds VC7.1 objects compiled from the
synthetic header and source stored beside them: the unmodified head and both variants for each atom.

- Each member is witnessed exactly by the functions whose code uses it: through an inline getter, a macro, `this->`,
  a derived class, or a virtual call.
- A call to an out-of-line function that uses the member is a named hold.
- Code that depends on the class size is held.
- Wrong offsets, swapped or foreign variants, unauthenticated head objects and rows that are not newly credited are
  all held.
