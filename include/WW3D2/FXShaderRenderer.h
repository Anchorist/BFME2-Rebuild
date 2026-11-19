// FXShaderRenderer queues mesh tasks for its three rendering passes.
#pragma once
#ifndef BFME2_FXSHADERRENDERER_H
#define BFME2_FXSHADERRENDERER_H

#include <vector>
#include "WWMath/Matrix3D.h"

class MeshClass;
class MeshModelClass;
namespace FXShader { class RenderingMethodDelegate; }

class FXShaderRenderer
{
public:
	FXShaderRenderer(void);
	~FXShaderRenderer(void);

	void Register_Mesh_Type(MeshModelClass *model);
	void Unregister_Mesh_Type(MeshModelClass *model);
	void Flush(void);

private:
	struct RenderingTask
	{
		RenderingTask(void);
		RenderingTask(const RenderingTask &other);
		~RenderingTask(void);
		RenderingTask &operator=(const RenderingTask &other);

		MeshClass *Mesh;
		int MethodCount;
		FXShader::RenderingMethodDelegate *Methods[6];
	};
	typedef char RenderingTaskSize[(sizeof(RenderingTask) == 0x20) ? 1 : -1];

	void PerformRendering(int first, int last);
	void FlushHardwareSkinnedRenderingTasks(void);
	void FlushSoftwareSkinnedRenderingTasks(void);
	void FlushRigidRenderingTasks(void);

	std::vector<RenderingTask> HardwareSkinnedTasks;
	std::vector<RenderingTask> SoftwareSkinnedTasks;
	std::vector<RenderingTask> RigidTasks;
	std::vector<Matrix3D> InstanceTransforms;
};

typedef char FXShaderRendererSize[(sizeof(FXShaderRenderer) == 0x30) ? 1 : -1];

extern FXShaderRenderer *TheFXShaderRenderer;

#endif
