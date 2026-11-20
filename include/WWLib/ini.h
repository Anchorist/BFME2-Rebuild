// ini.h: WWLib's INI file database (INIClass); the records are in inisup.h.
// Target facts (retail game.dat): INIClass is SIZE 0x10 with one virtual slot, the deleting
// destructor (scalar deleting body 0x00619100): vptr +0, the section list +4, the section
// index +8 and the file name +0xC (always a heap string; Initialize 0x006168F0 stores
// "<unknown>"). All three constructors (0x006169A0, 0x00619250 from a file, 0x00619280 from a
// name) call Initialize, then the file ones Load. The method list below is the set of rows
// ini.cpp's unit owns; signatures are read from the mangled names (Get_String has a buffer
// form 0x006171E0 and a StringClass form 0x00617260). Get_Section_List and Get_Section_Index
// are inline accessors that Registry's Load_Registry (0x0060FDC0) uses.
#pragma once
#ifndef BFME2_INI_H
#define BFME2_INI_H

#include <wchar.h>

class PKey;
class FileClass;
class Straw;
class Pipe;
class StringClass;
class WideStringClass;
struct INISection;
struct INIEntry;
template<class T> class TPoint3D;
template<class T> class TPoint2D;
template<class T> class TRect;
template<class T> class List;
template<class K, class V> class IndexClass;

class INIClass
{
public:
	INIClass();								// 0x006169A0
	INIClass(FileClass &file);						// 0x00619250
	INIClass(const char *filename);						// 0x00619280
	virtual ~INIClass();

	static void Keep_Blank_Entries(bool keep_blanks);

	int Load(FileClass &file);						// 0x00619120
	int Load(Straw &file);							// 0x00617B10
	int Load(const char *filename);						// 0x006191C0
	int Save(FileClass &file) const;					// 0x006165B0
	int Save(Pipe &pipe) const;						// 0x00615F20
	int Save(const char *filename) const;					// 0x00616650

	bool Clear(const char *section = 0, const char *entry = 0);
	bool Is_Loaded() const;
	bool Is_Present(const char *section, const char *entry = 0) const;
	int Entry_Count(const char *section) const;
	const char *Get_Entry(const char *section, int index) const;
	unsigned Enumerate_Entries(const char *section, const char *entry_prefix, unsigned startnumber = 0, unsigned endnumber = (unsigned)-1);
	PKey Get_PKey(bool fast) const;

	bool Get_Bool(const char *section, const char *entry, bool defvalue = false) const;
	float Get_Float(const char *section, const char *entry, float defvalue = 0.0f) const;
	double Get_Double(const char *section, const char *entry, double defvalue = 0.0) const;
	int Get_Hex(const char *section, const char *entry, int defvalue = 0) const;
	int Get_Int(const char *section, const char *entry, int defvalue = 0) const;
	int Get_String(const char *section, const char *entry, const char *defvalue, char *buffer, int size) const;	// 0x006171E0
	const StringClass &Get_String(StringClass &new_string, const char *section, const char *entry, const char *defvalue = "") const;	// 0x00617260
	const WideStringClass &Get_Wide_String(WideStringClass &new_string, const char *section, const char *entry, const wchar_t *defvalue = L"") const;
	int Get_List_Index(const char *section, const char *entry, const int defvalue, char *list[]);
	int *Get_Alloc_Int_Array(const char *section, const char *entry, int listend);
	int Get_Int_Bitfield(const char *section, const char *entry, int defvalue, char *list[]);
	char *Get_Alloc_String(const char *section, const char *entry, const char *defvalue) const;
	int Get_TextBlock(const char *section, char *buffer, int len) const;
	int Get_UUBlock(const char *section, void *buffer, int len) const;				// 0x00618500
	int Get_UUBlock(const char *section, const char *entry, void *block, int len) const;		// 0x00618A50
	TRect<int> Get_Rect(const char *section, const char *entry, const TRect<int> &defvalue) const;	// 0x00618DE0
	TPoint3D<int> Get_Point(const char *section, const char *entry, const TPoint3D<int> &defvalue) const;	// 0x00617790
	TPoint2D<int> Get_Point(const char *section, const char *entry, const TPoint2D<int> &defvalue) const;	// 0x00617680
	TPoint3D<float> Get_Point(const char *section, const char *entry, const TPoint3D<float> &defvalue) const;	// 0x006178C0
	TPoint2D<float> Get_Point(const char *section, const char *entry, const TPoint2D<float> &defvalue) const;	// 0x006179A0

	bool Put_Bool(const char *section, const char *entry, bool value);
	bool Put_Float(const char *section, const char *entry, float number);
	bool Put_Double(const char *section, const char *entry, double number);
	bool Put_Hex(const char *section, const char *entry, int number);
	bool Put_Int(const char *section, const char *entry, int number, int format = 0);
	bool Put_PKey(const PKey &key);
	bool Put_String(const char *section, const char *entry, const char *string);
	bool Put_TextBlock(const char *section, const char *text);
	bool Put_UUBlock(const char *section, const void *block, int len);				// 0x006183B0
	bool Put_UUBlock(const char *section, const char *entry, const void *block, int len);		// 0x00618970
	bool Put_Rect(const char *section, const char *entry, const TRect<int> &value);		// 0x00618D90
	bool Put_Point(const char *section, const char *entry, const TPoint3D<int> &value);		// 0x00617740
	bool Put_Point(const char *section, const char *entry, const TPoint3D<float> &value);		// 0x00617870
	bool Put_Point(const char *section, const char *entry, const TPoint2D<int> &value);		// 0x00617630
	bool Put_Wide_String(const char *section, const char *entry, const wchar_t *string);

	static const int MAX_LINE_LENGTH;

	List<INISection *> &Get_Section_List() { return *SectionList; }
	IndexClass<int, INISection *> &Get_Section_Index() { return *SectionIndex; }
	INISection *Find_Section(const char *section) const;
	INIEntry *Find_Entry(const char *section, const char *entry) const;

	static void Strip_Comments(char *buffer);
	static int CRC(const char *string);
	void DuplicateCRCError(const char *message, const char *section, const char *entry);

private:
	void Initialize();
	void Shutdown();

	List<INISection *> *SectionList;		// +0x04
	IndexClass<int, INISection *> *SectionIndex;	// +0x08
	INIClass(const INIClass &rvalue);
	INIClass operator=(const INIClass &rvalue);
	mutable char *Filename;			// +0x0C
	static bool KeepBlankEntries;
};
// SIZE 0x10

#endif
