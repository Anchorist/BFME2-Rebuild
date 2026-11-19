// Per-material FX shader setup. The 0x34-byte layout comes from allocations
// 0x152C64 and 0x15B129 and lifetime bodies 0x1525FB and 0x152411. Its ten-slot
// table at 0x7D3B1C has the RenderingMethod interface: slots 7 and 8 consume
// a method reference and return an empty reference, while slot 9 returns this.
#pragma once
#ifndef BFME2_FX_SHADER_SETUP_H
#define BFME2_FX_SHADER_SETUP_H

#include <vector>
#include "Common/AsciiString.h"
#include "WW3D2/FXShaderAsset.h"
#include "WW3D2/FXShaderParameter.h"
#include "WW3D2/RenderingMethod.h"
#include "WW3D2/TextureAsset.h"

class ChunkLoadClass;

class FXShaderSetup : public FXShader::RenderingMethod
{
public:
	FXShaderSetup();
	FXShaderSetup(const FXShaderSetup &other);
	FXShaderSetup &operator=(const FXShaderSetup &other);

	virtual bool Begin_Rendering(unsigned int *pass_count, int flags);
	virtual void Begin_Pass(unsigned int pass);
	virtual void UpdateDynamicParameterSet(unsigned int pass);
	virtual void End_Pass();
	virtual void End_Rendering();
	virtual void Set_Method(FXShader::RenderingMethodRef method);
	virtual FXShader::RenderingMethodRef Get_Method();
	virtual FXShader::RenderingMethod *Resolve_Method() { return this; }	// slot 9: 0x0047A6A9

	bool Load_W3D(ChunkLoadClass &chunk);

protected:
	virtual ~FXShaderSetup();

private:
	struct TextureBinding
	{
		const char *Parameter;
		TextureAsset Texture;
	};

	FXShaderAsset ShaderAsset;					// +0x08
	std::vector<FXShaderParameter> Parameters;	// +0x0C
	AsciiString TechniqueName;				// +0x18
	int LOD;							// +0x1C
	const char *Technique;					// +0x20
	const char *ParameterBlock;				// +0x24
	std::vector<TextureBinding> TextureBindings;	// +0x28
};

typedef char FXShaderSetupSize[(sizeof(FXShaderSetup) == 0x34) ? 1 : -1];

#endif
