// Native construction at 0xE6350 installs 0x7CEA04 and registers
// the Vegetation parameter namespace. Its destructor restores the
// shared namespace base table at 0x7C6F24 after unregistering it.
#pragma once
#ifndef BFME2_VEGETATION_FX_SHADER_PARAMETER_SOURCE_NAMESPACE_H
#define BFME2_VEGETATION_FX_SHADER_PARAMETER_SOURCE_NAMESPACE_H

#include "WW3D2/FXShaderParameterSourceNamespace.h"

class VegetationFXShaderParameterSourceNamespace : public FXShaderParameterSourceNamespace
{
public:
	VegetationFXShaderParameterSourceNamespace();
	virtual ~VegetationFXShaderParameterSourceNamespace();
	virtual void ResolveBindings(const char *name, const char *parameter, FXShaderParameterBinder *binder);
};

typedef char VegetationFXShaderParameterSourceNamespaceSize[
	(sizeof(VegetationFXShaderParameterSourceNamespace) == 4) ? 1 : -1];

#endif
