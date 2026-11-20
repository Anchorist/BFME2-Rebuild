// ProcessAnimateWindow.h: the animation styles AnimateWindowManager runs. Each one
// is an object with four operations per window (start, start in reverse, advance one
// frame, advance in reverse) and a handful of tuning members its constructor sets.
//
// Evidence (retail game.dat): the base's table 0x00874804 has six slots (deleting
// destructor 0x005C4F88, four pure virtuals, and the empty setMaxDuration folded to
// 0x0047A69C); each style's table (0x0087481C..0x008748D0) overrides the four and
// repeats slot 0. The constructors 0x005C5069 (right), 0x005C52CE (left), 0x005C55A5
// (top), 0x005C56B4 (bottom), 0x005C5F85 (top fast), 0x005C62D8 (right fast),
// 0x005C4FFF (spiral) and 0x005C4FEF (bottom timed) store the constants below; the
// vector members are named by which component they move (the right and left styles
// write x, top and bottom write y). Names are Zero Hour's (donor), values are retail's.
#pragma once
#ifndef BFME2_PROCESSANIMATEWINDOW_H
#define BFME2_PROCESSANIMATEWINDOW_H

#include "Common/Coord2D.h"

class AnimateWindow;

class ProcessAnimateWindow
{
public:
	ProcessAnimateWindow() {}											// 0x005C4F7F
	virtual ~ProcessAnimateWindow() {}									// slot 0, 0x005C4F88
	virtual void initAnimateWindow(AnimateWindow *animWin) = 0;			// slot 1
	virtual void initReverseAnimateWindow(AnimateWindow *animWin, unsigned int maxDelay = 0) = 0;	// slot 2
	virtual bool updateAnimateWindow(AnimateWindow *animWin) = 0;		// slot 3
	virtual bool reverseAnimateWindow(AnimateWindow *animWin) = 0;		// slot 4
	virtual void setMaxDuration(unsigned int maxDuration) {}			// slot 5, 0x0047A69C (folded `ret 4`)
};
// SIZE 0x04

// The five styles that share one tuning record: constructors 0x005C5069 and the
// like store these six words (+0x04..+0x14) and nothing else.
class ProcessAnimateWindowSlideFromRight : public ProcessAnimateWindow
{
public:
	ProcessAnimateWindowSlideFromRight();
	virtual void initAnimateWindow(AnimateWindow *animWin);
	virtual void initReverseAnimateWindow(AnimateWindow *animWin, unsigned int maxDelay = 0);
	virtual bool updateAnimateWindow(AnimateWindow *animWin);
	virtual bool reverseAnimateWindow(AnimateWindow *animWin);

	Coord2D m_maxVel;													// +0x04
	int m_slowDownThreshold;											// +0x0C
	float m_slowDownRatio;												// +0x10
	float m_speedUpRatio;												// +0x14
};
// SIZE 0x18

class ProcessAnimateWindowSlideFromRightFast : public ProcessAnimateWindow
{
public:
	ProcessAnimateWindowSlideFromRightFast();
	virtual void initAnimateWindow(AnimateWindow *animWin);
	virtual void initReverseAnimateWindow(AnimateWindow *animWin, unsigned int maxDelay = 0);
	virtual bool updateAnimateWindow(AnimateWindow *animWin);			// 0x005C64BE (shared with the right style)
	virtual bool reverseAnimateWindow(AnimateWindow *animWin);			// 0x005C51E5 (shared with the right style)

	Coord2D m_maxVel;													// +0x04
	int m_slowDownThreshold;											// +0x0C
	float m_slowDownRatio;												// +0x10
	float m_speedUpRatio;												// +0x14
};
// SIZE 0x18

class ProcessAnimateWindowSlideFromLeft : public ProcessAnimateWindow
{
public:
	ProcessAnimateWindowSlideFromLeft();
	virtual void initAnimateWindow(AnimateWindow *animWin);
	virtual void initReverseAnimateWindow(AnimateWindow *animWin, unsigned int maxDelay = 0);	// 0x005C5FC4 (shared with top, bottom and top fast)
	virtual bool updateAnimateWindow(AnimateWindow *animWin);
	virtual bool reverseAnimateWindow(AnimateWindow *animWin);

	Coord2D m_maxVel;													// +0x04
	int m_slowDownThreshold;											// +0x0C
	float m_slowDownRatio;												// +0x10
	float m_speedUpRatio;												// +0x14
};
// SIZE 0x18

class ProcessAnimateWindowSlideFromTop : public ProcessAnimateWindow
{
public:
	ProcessAnimateWindowSlideFromTop();
	virtual void initAnimateWindow(AnimateWindow *animWin);
	virtual void initReverseAnimateWindow(AnimateWindow *animWin, unsigned int maxDelay = 0);	// 0x005C5FC4
	virtual bool updateAnimateWindow(AnimateWindow *animWin);
	virtual bool reverseAnimateWindow(AnimateWindow *animWin);			// 0x005C61EE

	Coord2D m_maxVel;													// +0x04
	int m_slowDownThreshold;											// +0x0C
	float m_slowDownRatio;												// +0x10
	float m_speedUpRatio;												// +0x14
};
// SIZE 0x18

class ProcessAnimateWindowSlideFromTopFast : public ProcessAnimateWindow
{
public:
	ProcessAnimateWindowSlideFromTopFast();
	virtual void initAnimateWindow(AnimateWindow *animWin);
	virtual void initReverseAnimateWindow(AnimateWindow *animWin, unsigned int maxDelay = 0);
	virtual bool updateAnimateWindow(AnimateWindow *animWin);			// 0x005C6106 (shared with the top style)
	virtual bool reverseAnimateWindow(AnimateWindow *animWin);			// (shared with the top style)

	Coord2D m_maxVel;													// +0x04
	int m_slowDownThreshold;											// +0x0C
	float m_slowDownRatio;												// +0x10
	float m_speedUpRatio;												// +0x14
};
// SIZE 0x18

class ProcessAnimateWindowSlideFromBottom : public ProcessAnimateWindow
{
public:
	ProcessAnimateWindowSlideFromBottom();
	virtual void initAnimateWindow(AnimateWindow *animWin);
	virtual void initReverseAnimateWindow(AnimateWindow *animWin, unsigned int maxDelay = 0);	// 0x005C5FC4
	virtual bool updateAnimateWindow(AnimateWindow *animWin);
	virtual bool reverseAnimateWindow(AnimateWindow *animWin);

	Coord2D m_maxVel;													// +0x04
	int m_slowDownThreshold;											// +0x0C
	float m_slowDownRatio;												// +0x10
	float m_speedUpRatio;												// +0x14
};
// SIZE 0x18

class ProcessAnimateWindowSpiral : public ProcessAnimateWindow
{
public:
	ProcessAnimateWindowSpiral();										// 0x005C4FFF
	virtual void initAnimateWindow(AnimateWindow *animWin);
	virtual void initReverseAnimateWindow(AnimateWindow *animWin, unsigned int maxDelay = 0);
	virtual bool updateAnimateWindow(AnimateWindow *animWin);
	virtual bool reverseAnimateWindow(AnimateWindow *animWin);

	float m_deltaTheta;													// +0x04
	int m_maxR;															// +0x08 (half the display width)
};
// SIZE 0x0C

class ProcessAnimateWindowSlideFromBottomTimed : public ProcessAnimateWindow
{
public:
	ProcessAnimateWindowSlideFromBottomTimed();							// 0x005C4FEF
	virtual void initAnimateWindow(AnimateWindow *animWin);
	virtual void initReverseAnimateWindow(AnimateWindow *animWin, unsigned int maxDelay = 0);
	virtual bool updateAnimateWindow(AnimateWindow *animWin);
	virtual bool reverseAnimateWindow(AnimateWindow *animWin);			// 0x005CB265 (a folded body shared with other classes)
	virtual void setMaxDuration(unsigned int maxDuration);				// 0x002B230F

	unsigned int m_maxDuration;											// +0x04, 1000 after construction
};
// SIZE 0x08

#endif
