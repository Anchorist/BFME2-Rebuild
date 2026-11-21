// cl: /O1
#include "Common/Xfer.h"
// The typed transfer operators of Xfer. Each passes the value to the XferData virtual with a four character tag for
// its type ('byte', 'ubyt', 'bool', 'int', 'i64', 'uint', 'shrt', 'usht', 'real') and its size.
// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G0000546C name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x0000546C size=28 name=??8Xfer@@UAEAAV0@AAD@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Xfer &Xfer::operator==(char &value)
{
	XferData('byte', &value, sizeof(char));
	return *this;
}
// FUNCTION: BFME2 0x00005488 size=28 name=??8Xfer@@UAEAAV0@AAE@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Xfer &Xfer::operator==(unsigned char &value)
{
	XferData('ubyt', &value, sizeof(unsigned char));
	return *this;
}
// FUNCTION: BFME2 0x000054A4 size=28 name=??8Xfer@@UAEAAV0@AA_N@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Xfer &Xfer::operator==(bool &value)
{
	XferData('bool', &value, sizeof(bool));
	return *this;
}
// FUNCTION: BFME2 0x000054C0 size=28 name=??8Xfer@@UAEAAV0@AAH@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Xfer &Xfer::operator==(int &value)
{
	XferData('int', &value, sizeof(int));
	return *this;
}
// FUNCTION: BFME2 0x000054DC size=28 name=??8Xfer@@UAEAAV0@AA_J@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Xfer &Xfer::operator==(__int64 &value)
{
	XferData('i64', &value, sizeof(__int64));
	return *this;
}
// FUNCTION: BFME2 0x000054F8 size=28 name=??8Xfer@@UAEAAV0@AAI@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Xfer &Xfer::operator==(unsigned int &value)
{
	XferData('uint', &value, sizeof(unsigned int));
	return *this;
}
// FUNCTION: BFME2 0x00005514 size=28 name=??8Xfer@@UAEAAV0@AAF@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Xfer &Xfer::operator==(short &value)
{
	XferData('shrt', &value, sizeof(short));
	return *this;
}
// FUNCTION: BFME2 0x00005530 size=28 name=??8Xfer@@UAEAAV0@AAG@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Xfer &Xfer::operator==(unsigned short &value)
{
	XferData('usht', &value, sizeof(unsigned short));
	return *this;
}
// FUNCTION: BFME2 0x0000554C size=28 name=??8Xfer@@UAEAAV0@AAM@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
Xfer &Xfer::operator==(float &value)
{
	XferData('real', &value, sizeof(float));
	return *this;
}
