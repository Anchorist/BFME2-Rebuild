// DataChunk.h: the map-file chunk reader and writer, and the chunk-name table they share.
// Target facts (retail RVAs; layouts from the constructors and the chunk-stack accessors):
// - DataChunkTableOfContents (SIZE 0x10): constructor 0x00306D48 stores a null
//   list head at +0, a zero count at +4, next ID 1 at +8 and false at +0xC.
//   The destructor 0x00306D5C frees the mapping list at +0.
// - DataChunkInput (SIZE 0x28, no virtual functions): stream at +0, the table at +4,
//   the stream's tell result at +0x14, the parser list at +0x18, the chunk stack at
//   +0x1C, and two user pointers at +0x20 and +0x24.
// - InputChunk: vtable at +0 (virtual destructor, deleted with ::delete), next chunk
//   at +4, ID at +8, version word at +0xC, data size at +0x14, bytes left at +0x18.
// - DataChunkOutput (SIZE 0x1C, no virtual functions): stream at +0, FILE at +4, the
//   table at +8, the output chunk stack at +0x18.
#pragma once
#ifndef BFME2_COMMON_DATACHUNK_H
#define BFME2_COMMON_DATACHUNK_H

#include <stdio.h>
#include "Common/GameType.h"
#include "Common/AsciiString.h"
#include "Common/ChunkInputStream.h"
#include "Common/Dict.h"

class UnicodeString;
class Dict;
class OutputStream;
class UserParser;
class OutputChunk;

class DataChunkInput;

typedef unsigned short DataChunkVersionType;
typedef bool (*DataChunkParserPtr)(DataChunkInput &file, struct DataChunkInfo *info, void *userData);

// What a registered parser is handed for the chunk it is called on (the locals DataChunkInput::parse 0x00307AC0 fills; Zero Hour's DataChunkInfo).
struct DataChunkInfo
{
	AsciiString m_label;						// +0x00
	AsciiString m_parentLabel;					// +0x04
	DataChunkVersionType m_version;				// +0x08
	UnsignedInt m_dataSize;						// +0x0C
};
// SIZE 0x10

class InputChunk
{
public:
	virtual ~InputChunk() {}					// retail's deleting destructor is the one ::delete calls

	InputChunk *m_next;							// +0x04
	UnsignedInt m_id;							// +0x08
	UnsignedShort m_version;					// +0x0C
	UnsignedByte m_unknown0E[2];				// +0x0E, not yet recovered
	UnsignedInt m_filePos;						// +0x10, stream position of the chunk's data
	UnsignedInt m_dataSize;						// +0x14
	Int m_dataLeft;								// +0x18, signed: the end test compares it with zero
};

// One entry of the chunk-name table. The concrete object is allocated elsewhere, so the
// destructor is virtual and the table deletes entries with ::delete.
class Mapping
{
public:
	virtual ~Mapping() {}

	Mapping *m_next;							// +0x04
	AsciiString m_name;							// +0x08
	UnsignedInt m_id;							// +0x0C
};
// SIZE 0x10

class DataChunkTableOfContents
{
public:
	DataChunkTableOfContents();					// 0x00306D48
	~DataChunkTableOfContents();

	UnsignedInt getID(const AsciiString &name);
	AsciiString getName(UnsignedInt id);
	UnsignedInt allocateID(const AsciiString &name);
	Bool isOpenedForRead() const { return m_headerOpened; }
	void write(OutputStream &stream);
	void read(ChunkInputStream &stream);

	Mapping *m_list;							// +0x00
	Int m_listLength;							// +0x04
	UnsignedInt m_nextID;						// +0x08
	Bool m_headerOpened;						// +0x0C

private:
	Mapping *findMapping(const AsciiString &name);
};
// SIZE 0x10

// A registered chunk parser. The parsers form a list headed in the input; each entry
// also records the field that points at it, so it can be unlinked.
class UserParser
{
public:
	UserParser();								// 0x00307371
	virtual ~UserParser();

	UserParser *m_next;							// +0x04
	UserParser **m_link;						// +0x08, the pointer field that refers to this entry
	DataChunkParserPtr m_parser;				// +0x0C
	AsciiString m_label;						// +0x10
	AsciiString m_parentLabel;					// +0x14
	void *m_userData;							// +0x18
};
// SIZE 0x1C

class DataChunkInput
{
public:
	DataChunkInput(ChunkInputStream *stream);	// 0x00307316
	~DataChunkInput();

	Bool atEndOfFile();
	Bool atEndOfChunk();
	void reset();
	void clearChunkStack();
	AsciiString getChunkLabel();
	DataChunkVersionType getChunkVersion();
	UnsignedInt getChunkDataSize();
	UnsignedInt getChunkDataSizeLeft();
	Real readReal();
	Int readInt();
	UnsignedByte readByte();
	void readArrayOfBytes(char *buffer, Int length);
	NameKeyType readNameKey();
	AsciiString readAsciiString();
	Bool parse(void *userData);
	UnicodeString readUnicodeString();
	Dict readDict();
	AsciiString openDataChunk(DataChunkVersionType *version);
	UserParser *registerParser(const AsciiString &label, const AsciiString &parentLabel,
		DataChunkParserPtr parser, void *userData);	// 0x00307779

protected:
	void decrementDataLeft(Int size);
	void closeDataChunk();

	ChunkInputStream *m_file;					// +0x00
	DataChunkTableOfContents m_contents;		// +0x04
	Int m_fileposOfFirstChunk;					// +0x14
	UserParser *m_parserList;					// +0x18
	InputChunk *m_chunkStack;					// +0x1C
	void *m_currentObject;						// +0x20
	void *m_userData;							// +0x24
};
// SIZE 0x28

class OutputChunk
{
public:
	virtual ~OutputChunk() {}

	OutputChunk *m_next;						// +0x04
	UnsignedInt m_id;							// +0x08, the chunk's name ID
	Int m_fileStart;							// +0x0C, file position of the chunk's size field
};

class DataChunkOutput
{
public:
	DataChunkOutput(OutputStream *stream);		// 0x00306FA5
	~DataChunkOutput();							// 0x00307680

	void openDataChunk(char *name, DataChunkVersionType version);
	void closeDataChunk();
	void writeByte(UnsignedByte value);
	void writeArrayOfBytes(char *buffer, Int length);
	void writeAsciiString(const AsciiString &text) throw();
	void writeUnicodeString(UnicodeString text);
	void writeInt(Int value);					// 0x00306CFF (folded with writeReal)
	void writeReal(Real value);					// 0x00306CFF (folded with writeInt)
	void writeDict(const Dict &d);
	void writeNameKey(NameKeyType key);

protected:
	OutputStream *m_pOut;						// +0x00
	FILE *m_tmp_file;							// +0x04
	DataChunkTableOfContents m_contents;		// +0x08
	OutputChunk *m_chunkStack;					// +0x18
};
// SIZE 0x1C

#endif
