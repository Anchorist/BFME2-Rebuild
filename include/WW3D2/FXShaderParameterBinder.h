// Effect parameter bindings are grouped by technique and six dynamic sets.
// Native 0x153F08 loads each 0x4C-byte technique record and supplies a
// temporary parsing context at +0x10. Native 0x15326D invokes the callback
// in each eight-byte binding with the current effect and parameter.
#pragma once
#ifndef BFME2_FX_SHADER_PARAMETER_BINDER_H
#define BFME2_FX_SHADER_PARAMETER_BINDER_H

#include <vector>
#include "Apt/AptRef.h"

struct ID3DXEffect;

class FXShaderBindingFunction : public AptRefTarget
{
public:
	virtual void Apply(ID3DXEffect *effect, const char *parameter) = 0;
};

class FXShaderParameterBinder
{
public:
	explicit FXShaderParameterBinder(ID3DXEffect *effect);
	~FXShaderParameterBinder();

	void Init(ID3DXEffect *effect);
	void ResolveBindings(const char *name, const char *parameter);
	void PushDynamicSetStack(int set);
	void PopDynamicSetStack();

private:
	struct Binding
	{
		AptRef<FXShaderBindingFunction> Function;
		const char *Parameter;
	};

	struct TechniqueBindings
	{
		const char *Technique;
		std::vector<Binding> DynamicSets[6];
	};

	struct ParsingContext
	{
		const char *CurrentParameter;
		std::vector<int> DynamicSetStack;
	};

	typedef char BindingSize[(sizeof(Binding) == 0x08) ? 1 : -1];
	typedef char TechniqueBindingsSize[(sizeof(TechniqueBindings) == 0x4C) ? 1 : -1];
	typedef char ParsingContextSize[(sizeof(ParsingContext) == 0x10) ? 1 : -1];

	ID3DXEffect *Effect;						// +0x00 held COM reference
	std::vector<TechniqueBindings> Techniques;	// +0x04
	ParsingContext *CurrentContext;				// +0x10 borrowed while resolving
};

typedef char FXShaderParameterBinderSize[(sizeof(FXShaderParameterBinder) == 0x14) ? 1 : -1];

#endif
