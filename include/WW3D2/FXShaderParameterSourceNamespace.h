// The two-slot namespace interface used by the effect parameter binder.
// The base lifetime restores 0x7C6F24. Each concrete namespace provides its
// own ResolveBindings through slot 1.
#pragma once
#ifndef BFME2_FX_SHADER_PARAMETER_SOURCE_NAMESPACE_H
#define BFME2_FX_SHADER_PARAMETER_SOURCE_NAMESPACE_H

class FXShaderParameterBinder;

class FXShaderParameterSourceNamespace
{
public:
	virtual ~FXShaderParameterSourceNamespace() {}
	virtual void ResolveBindings(const char *name, const char *parameter, FXShaderParameterBinder *binder) = 0;
};

typedef char FXShaderParameterSourceNamespaceSize[(sizeof(FXShaderParameterSourceNamespace) == 4) ? 1 : -1];

void Register_FX_Shader_Parameter_Source(const char *name, FXShaderParameterSourceNamespace *source);
void Unregister_FX_Shader_Parameter_Source(const char *name);

#endif
