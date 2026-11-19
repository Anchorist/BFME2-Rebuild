// The WW3D effect parameter namespace and its embedded Fog namespace.
// Native constructor 0x18BEC7 installs tables 0x7D5BE4 and 0x7D5BD4 at
// +0 and +4. The opacity binding 0x18BDA0 passes the float at +8 to SetFloat.
#pragma once
#ifndef BFME2_FX_SHADER_PARAMETER_SOURCE_NAMESPACE_WW3D_H
#define BFME2_FX_SHADER_PARAMETER_SOURCE_NAMESPACE_WW3D_H

#include "WW3D2/FXShaderParameterSourceNamespace.h"

struct ID3DXEffect;

class FXShaderParameterSourceNamespaceWW3D : public FXShaderParameterSourceNamespace
{
public:
	FXShaderParameterSourceNamespaceWW3D();
	virtual ~FXShaderParameterSourceNamespaceWW3D();
	virtual void ResolveBindings(const char *name, const char *parameter, FXShaderParameterBinder *binder);

	void Apply_Opacity_Override(ID3DXEffect *effect, const char *parameter);

private:
	class SourceNamespace_Fog : public FXShaderParameterSourceNamespace
	{
	public:
		virtual void ResolveBindings(const char *name, const char *parameter, FXShaderParameterBinder *binder);
	};

	SourceNamespace_Fog Fog;
	float OpacityOverride;
};

typedef char FXShaderParameterSourceNamespaceWW3DSize[(sizeof(FXShaderParameterSourceNamespaceWW3D) == 0x0C) ? 1 : -1];

#endif
