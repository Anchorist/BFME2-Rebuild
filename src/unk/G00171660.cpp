// cl: /O2
// stlport46
#include "WW3D2/MeshModelClass.h"
#include "WW3D2/DX8TextureCategoryClass.h"
#include "WW3D2/DX8FVFCategoryContainer.h"
#include "WW3D2/DX8MeshRendererClass.h"
#include "WW3D2/FXShaderRenderer.h"

bool Restore_FXShader_Pass0(MeshMatDescClass *material);

// Generated from the ledger; map snapshot c591f7146f88c8a8248ebb8ae22f0c978c22aed463db64e05ef57ff0dfae99cc
// object=G00171660 name-evidence=invented
// Extents and edges are hypotheses; byte verification alone does not establish original TU boundaries.
// FUNCTION: BFME2 0x00171660 size=6 name=?Rva00171660Get@@YAHXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00171670 size=6 name=?Rva00171670GetByte@@YAEXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00171680 size=11 name=?Set_Single_Material@MeshModelClass@@QAEXPAVVertexMaterialClass@@H@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x00171690 size=11 name=?Set_Material@MeshModelClass@@QAEXHPAVVertexMaterialClass@@H@Z evidence=N:ledger tier=B hypothesis:mm1-gap-unit
// FUNCTION: BFME2 0x001716E0 size=58 name=?rva001716E0UnregisterMeshModel@MeshModelClass@@QAEXXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
void MeshModelClass::Unregister_For_Rendering(void)
{
	if (TheDX8MeshRenderer) {
		TheDX8MeshRenderer->Unregister_Mesh_Type(this);
	}
	if (TheFXShaderRenderer) {
		TheFXShaderRenderer->Unregister_Mesh_Type(this);
	}
	if (CurMatDesc->Has_Stored_Pass0_State()) {
		Restore_FXShader_Pass0(CurMatDesc);
	}
}
// FUNCTION: BFME2 0x00171720 size=55 name=?rva00171720@MeshModelClass@@QAE_NXZ evidence=?:placeholder tier=B hypothesis:mm1-gap-unit
