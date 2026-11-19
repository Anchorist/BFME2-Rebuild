// Portions derived from Command & Conquer Generals Zero Hour, (c) Electronic Arts Inc., GPL-3.0-or-later; see LICENSE and NOTICE.
// 0x65A39 constructs the nested shaker with the MultiListObject base, then
// Position at +8, four scalars at +0x14 through +0x20, Omega at +0x24 and
// Phi at +0x30. Its own table 0x7C5C74 contains the deleting destructor.
#pragma once
#ifndef BFME2_CAMERA_SHAKE_SYSTEM_H
#define BFME2_CAMERA_SHAKE_SYSTEM_H

#include "WWLib/multilist.h"
#include "WWMath/Vector3.h"

class CameraShakeSystemClass
{
public:
	CameraShakeSystemClass();
	~CameraShakeSystemClass();

	void Add_Camera_Shake(const Vector3 &position, float radius = 50.0f,
		float duration = 1.5f, float intensity = 1.0f);
	void Timestep(float dt);
	bool IsCameraShaking();
	void Update_Camera_Shaker(Vector3 position, Vector3 *angles);

	class CameraShakerClass : public MultiListObjectClass, public AutoPoolClass<CameraShakerClass, 256>
	{
	public:
		CameraShakerClass(const Vector3 &position, float radius, float duration, float intensity);
		virtual ~CameraShakerClass();

		void Timestep(float dt);
		bool Is_Expired();
		void Compute_Rotations(const Vector3 &position, Vector3 *angles);

	private:
		Vector3 Position;
		float Radius;
		float Duration;
		float Intensity;
		float ElapsedTime;
		Vector3 Omega;
		Vector3 Phi;
	};

	typedef char CameraShakerClassSize[(sizeof(CameraShakerClass) == 0x3C) ? 1 : -1];

protected:
	MultiListClass<CameraShakerClass> CameraShakerList;
};

typedef char CameraShakeSystemClassSize[(sizeof(CameraShakeSystemClass) == 0x18) ? 1 : -1];

#endif
