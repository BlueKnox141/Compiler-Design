"""Symbol Table implementation.

Stores declared variables with their name, type (always 'int'), and initial value
(literal constant string or '-' if uninitialized/non-literal).
"""

from typing import List, Dict, Optional, NamedTuple


class SymbolTableEntry(NamedTuple):
    name: str
    type: str
    value: str


class SymbolTable:
    """Symbol Table recording variable name, type, and initializer value."""

    def __init__(self):
        self.entries: List[SymbolTableEntry] = []
        self._by_name: Dict[str, SymbolTableEntry] = {}

    def insert(self, name: str, var_type: str = "int", value: str = "-") -> SymbolTableEntry:
        """Insert a new symbol entry."""
        entry = SymbolTableEntry(name, var_type, value)
        self.entries.append(entry)
        self._by_name[name] = entry
        return entry

    def lookup(self, name: str) -> Optional[SymbolTableEntry]:
        """Look up a symbol by name."""
        return self._by_name.get(name)

    def format_table(self) -> str:
        """Format the symbol table matching the required layout.

        Heading: Name Type Value
        Followed by entries in declaration order.
        """
        lines = ["Name Type Value"]
        for entry in self.entries:
            lines.append(f"{entry.name} {entry.type} {entry.value}")
        return "\n".join(lines)
