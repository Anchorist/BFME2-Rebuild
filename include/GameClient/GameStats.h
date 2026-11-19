// Rows of values and labels shown by the statistics screens.
#pragma once

#include <vector>
#include "Common/GameType.h"
#include "Common/UnicodeString.h"

class GameWindow;

namespace GameStats
{
	struct Cell
	{
		UnicodeString m_label;
		Real m_value;
	};

	struct Row
	{
		void Init(const char *label, Int columnCount);

		UnicodeString m_label;
		std::vector<Cell> m_cells;
		Real m_maximum;
		Bool m_hasValues;
	};

	class Table
	{
	public:
		Table(UnsignedInt rowCount);
		virtual ~Table();

	protected:
		std::vector<Row> m_rows;
		GameWindow *m_listBox;
	};

	class Persistent : public Table
	{
	public:
		Persistent(Int columnCount);
		virtual ~Persistent();
		void CalculateTotalColumn(Real scale);

	protected:
		Int m_lastColumn;
	};

	typedef char CellSizeCheck[sizeof(Cell) == 0x8 ? 1 : -1];
	typedef char RowSizeCheck[sizeof(Row) == 0x18 ? 1 : -1];
	typedef char TableSizeCheck[sizeof(Table) == 0x14 ? 1 : -1];
	typedef char PersistentSizeCheck[sizeof(Persistent) == 0x18 ? 1 : -1];
}
