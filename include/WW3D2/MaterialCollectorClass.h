// MaterialCollectorClass.h: gathers the distinct shaders, vertex materials
// and textures of mesh models (matinfo.cpp).
//
// Target facts:
// - The constructor 0x00170240 builds a DynamicVectorClass of shaders at +0
//   (VectorClass constructor 0x0016FB40, vftable 0x007D46A0), one of vertex
//   material pointers at +0x18 inline (vftable 0x007D4658) and one of texture
//   handles at +0x30 (0x0016ED80, vftable 0x007D4688); then the last-added
//   shader +0x48, vertex material +0x4C and texture +0x50. SIZE 0x54.
// - Peek_Shader 0x0016F4C0, Peek_Vertex_Material 0x0016F510 and
//   Find_Vertex_Material 0x0016F550 index the vectors' data pointers (+4,
//   +0x1C) and Find_Vertex_Material walks the +0x28 count; Reset 0x0016F460
//   releases every vertex material, then clears +0x30, +0x18 and +0 through
//   their Clear slot.
// - Add_Shader 0x0016FCD0 and Add_Vertex_Material 0x0016FD30 skip the
//   last-added entry, search, and append with DynamicVectorClass::Add out of
//   line (0x001A3A60).
#pragma once
#ifndef BFME2_MATERIALCOLLECTORCLASS_H
#define BFME2_MATERIALCOLLECTORCLASS_H

#include "WWLib/vector.h"
#include "WW3D2/ShaderClass.h"
#include "WW3D2/TextureAsset.h"

class VertexMaterialClass;
class MeshModelClass;

class MaterialCollectorClass
{
public:
	MaterialCollectorClass(void);							// 0x00170240
	~MaterialCollectorClass(void);

	void Reset(void);
	void Collect_Materials(MeshModelClass *mesh);

	void Add_Shader(ShaderClass shader);
	void Add_Vertex_Material(VertexMaterialClass *vmat);

	int Get_Shader_Count(void) { return Shaders.Count(); }
	int Get_Vertex_Material_Count(void) { return VertexMaterials.Count(); }
	int Get_Texture_Count(void) { return Textures.Count(); }

	ShaderClass Peek_Shader(int i);
	VertexMaterialClass *Peek_Vertex_Material(int i);

	TextureAsset Peek_Texture(int i);
	int Find_Texture(const TextureAsset &tex);
	void Add_Texture(const TextureAsset &tex);

	int Find_Vertex_Material(VertexMaterialClass *vmat);
	int Find_Shader(ShaderClass shader)						// Zero Hour's inline search; Add_Shader 0x0016FCD0 expands it in place
	{
		for (int index = 0; index < Shaders.Count(); index++) {
			if (Shaders[index] == shader) return index;
		}
		return -1;
	}

protected:
	DynamicVectorClass<ShaderClass> Shaders;			// +0x00
	DynamicVectorClass<VertexMaterialClass *> VertexMaterials;	// +0x18
	DynamicVectorClass<TextureAsset> Textures;			// +0x30
	ShaderClass LastShader;						// +0x48
	VertexMaterialClass *LastMaterial;				// +0x4C
	TextureAsset LastTexture;					// +0x50
};

typedef char MaterialCollectorClassSize[(sizeof(MaterialCollectorClass) == 0x54) ? 1 : -1];

#endif
