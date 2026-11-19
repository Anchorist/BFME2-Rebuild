// The rendering-method interface used by FXShaderSetup and the delegate.
// Native tables 0x7D3B1C and 0x7C6540 share the ten slots below. The first
// two come from RefCountClass. A method reference owns one RefCountClass
// reference (copy and release at 0x72A94); the delegate stores it at +8.
#pragma once
#ifndef BFME2_RENDERING_METHOD_H
#define BFME2_RENDERING_METHOD_H

#include "WWLib/RefCountClass.h"

namespace FXShader
{

class RenderingMethodRef;

class RenderingMethod : public RefCountClass
{
public:
	virtual bool Begin_Rendering(unsigned int *pass_count, int flags) = 0;
	virtual void Begin_Pass(unsigned int pass) = 0;
	virtual void UpdateDynamicParameterSet(unsigned int pass) = 0;
	virtual void End_Pass() = 0;
	virtual void End_Rendering() = 0;
	virtual void Set_Method(RenderingMethodRef method) = 0;
	virtual RenderingMethodRef Get_Method() = 0;
	virtual RenderingMethod *Resolve_Method() = 0;

protected:
	virtual ~RenderingMethod() {}
};

class RenderingMethodRef
{
public:
	RenderingMethodRef() : Method(0) {}
	RenderingMethodRef(const RenderingMethodRef &other) : Method(other.Method)
	{
		if (Method)
			Method->Add_Ref();
	}
	~RenderingMethodRef()
	{
		if (Method)
			Method->Release_Ref();
	}

	RenderingMethodRef &operator=(const RenderingMethodRef &other);
	RenderingMethod *Get() const { return Method; }

private:
	RenderingMethod *Method;
};

class RenderingMethodDelegate : public RenderingMethod
{
public:
	RenderingMethodDelegate();
	virtual bool Begin_Rendering(unsigned int *pass_count, int flags);
	virtual void Begin_Pass(unsigned int pass);
	virtual void UpdateDynamicParameterSet(unsigned int pass);
	virtual void End_Pass();
	virtual void End_Rendering();
	virtual void Set_Method(RenderingMethodRef method);
	virtual RenderingMethodRef Get_Method();
	virtual RenderingMethod *Resolve_Method();

private:
	RenderingMethodRef Target;
};

typedef char RenderingMethodSize[(sizeof(RenderingMethod) == 8) ? 1 : -1];
typedef char RenderingMethodRefSize[(sizeof(RenderingMethodRef) == 4) ? 1 : -1];
typedef char RenderingMethodDelegateSize[(sizeof(RenderingMethodDelegate) == 12) ? 1 : -1];

}

#endif
