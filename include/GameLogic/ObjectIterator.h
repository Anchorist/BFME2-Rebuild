#pragma once

#include "GameLogic/ObjectIteratorData.h"

class Object;

class ObjectIterator
{
public:
    ObjectIterator();
    ObjectIterator(const ObjectIterator &other);
    ~ObjectIterator();

    unsigned count() const { return m_data->m_objects.size(); }
    Object *next() throw();

private:
    ObjectIteratorData *m_data;
};

typedef char ObjectIteratorSize[(sizeof(ObjectIterator) == 0x04) ? 1 : -1];
