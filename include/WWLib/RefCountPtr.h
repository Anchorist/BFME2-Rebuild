// Portions derived from Command & Conquer Generals and Command & Conquer Generals Zero Hour, (c) Electronic Arts Inc., GPL-3.0-or-later; see LICENSE and NOTICE.
#pragma once

// WWLib/ref_ptr.h. A copied element adds a reference at 0x00087A5C.
// The water vectors release each element in the 0x000806B4 destructor path.
template <class T>
class RefCountPtr
{
public:
	RefCountPtr() : Referent(0) {}

	RefCountPtr(const RefCountPtr &rhs) : Referent(rhs.Referent)
	{
		if (Referent)
			Referent->Add_Ref();
	}

	const RefCountPtr &operator=(const RefCountPtr &rhs)
	{
		if (rhs.Referent)
			rhs.Referent->Add_Ref();
		if (Referent)
			Referent->Release_Ref();
		Referent = rhs.Referent;
		return *this;
	}

	~RefCountPtr()
	{
		if (Referent)
			Referent->Release_Ref();
	}

private:
	T *Referent;
};
