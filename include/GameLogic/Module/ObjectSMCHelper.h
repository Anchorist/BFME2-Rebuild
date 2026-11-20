// ObjectSMCHelper: the helper module that times an object's special model conditions (Object::m_smcHelper;
// Object::setSpecialModelConditionState forwards to setModelConditionState). SIZE 0x24: ObjectHelper (0x20) and a
// std::list at +0x20 whose nodes hold the model condition and the frame it ends. update ends every entry whose frame has
// passed, framesUntilNext returns the smallest frame, and xfer saves the count and then each (condition, frame) pair. The
// destructor resets the tables and destroys the list.
#pragma once
#ifndef BFME2_OBJECTSMCHELPER_H
#define BFME2_OBJECTSMCHELPER_H

#include <list>
#include "GameLogic/Module/ObjectHelper.h"

class Object;
class Thing;
class Xfer;
enum ModelConditionFlagType;

class ObjectSMCHelper : public ObjectHelper
{
public:
	ObjectSMCHelper(Thing *thing, const ModuleData *moduleData);
	virtual ~ObjectSMCHelper();
	virtual NameKeyType getModuleNameKey() const;						// slot 4
	virtual UpdateSleepTime update();
	void setModelConditionState(ModelConditionFlagType flag, UnsignedInt frames);

protected:
	virtual void loadPostProcess() { ObjectHelper::loadPostProcess(); }	// slot 1: the helper forwarder that jumps to ObjectHelper's own, like the other helpers
	virtual const char *GetSnapshotName() const;						// slot 2
	virtual void xfer(Xfer *xfer);

private:
	struct Entry
	{
		Int m_flag;														// +0x8 of the list node: the model condition
		UnsignedInt m_frame;											// +0xC the frame it ends
	};
	Int framesUntilNext();
	_STL::list<Entry> m_entries;										// +0x20
};
typedef char ObjectSMCHelper_size[(sizeof(ObjectSMCHelper) == 0x24) ? 1 : -1];

#endif
