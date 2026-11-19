// FXShaderGeometry owns the prepared geometry of one mesh for the FX shader renderer.
#pragma once
#ifndef BFME2_FXSHADERGEOMETRY_H
#define BFME2_FXSHADERGEOMETRY_H

#include <vector>

struct IDirect3DVertexDeclaration9;
class VertexBufferClass;
class IndexBufferClass;
class MeshModelClass;

class FXShaderGeometry
{
public:
	FXShaderGeometry(void);
	~FXShaderGeometry(void);

	bool Init(MeshModelClass *mesh);
	void Begin_Rendering(unsigned short vertex_offset);

private:
	bool Skin;
	unsigned int FVF;
	IDirect3DVertexDeclaration9 *Declaration;
	VertexBufferClass *VertexBuffer;
	IndexBufferClass *IndexBuffer;
	std::vector<short> BoneIndices;
	int BonesPerVertex;
	int InstanceCount;
};

typedef char FXShaderGeometrySize[(sizeof(FXShaderGeometry) == 0x28) ? 1 : -1];

#endif
