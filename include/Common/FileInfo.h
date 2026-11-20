#pragma once
// Target file-system output: four unsigned words.
// GameTextManager embeds this record at+C..+1B. No constructor or vptr.
struct FileInfo {
    unsigned int sizeHigh, sizeLow;
    unsigned int timestampHigh, timestampLow;
};
typedef char FileInfoSize[sizeof(FileInfo)==0x10 ? 1 : -1];
