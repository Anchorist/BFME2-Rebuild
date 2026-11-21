"""Optional H6 refinement for indexed members and base forwards in virtual slots."""
from dataclasses import dataclass
import re

from header_inline import BehaviorEvidence, body_values, field_reference, fingerprint, shape

UINT = re.compile(r"(?:0|[1-9][0-9]*|0[xX][0-9a-fA-F]+)\Z")
NAME = re.compile(r"(?:[A-Za-z_]\w*::)+[A-Za-z_]\w*\Z", re.ASCII)
SLOT_REQUIRED = "This virtual base forward needs a verified retail table slot and target."


@dataclass(frozen=True, order=True)
class ArrayMember:
    name: str
    length: int
    builtin_elements: bool


@dataclass(frozen=True, order=True)
class VirtualSlot:
    """Protected, typed slot corroboration for the exact patched function."""
    body: BehaviorEvidence
    table_owner: str
    table_rva: int
    index: int
    selected_base: str
    expected_target_rva: int
    emitted_target_rva: int
    offset_to_subobject: int
    witnessing_row_rva: int
    newly_credited_reference_pass: bool


def body_key(record):
    return BehaviorEvidence(record.path, record.line, record.qualified,
                            record.signature, fingerprint(record))


def indexed_member(record, arrays):
    if record.initializers.strip():
        return False
    source, values = body_values(record)
    if (list(source.directives()) or len(values) < 7 or values[:2] != ("{", "return")
            or values[-5] != "[" or values[-3:] != ("]", ";", "}") or not UINT.fullmatch(values[-4])):
        return False
    expression = values[2:-5]
    if not field_reference(expression, record.fields, record.parameters):
        return False
    number = values[-4]
    if len(number) > 12:
        return False
    index = int(number, 16 if number.lower().startswith("0x") else 10)
    known = tuple(array for array in arrays if array.name == expression[-1])
    return len(known) == 1 and known[0].builtin_elements is True and 0 <= index < known[0].length


def forwarded_base(record):
    source, values = body_values(record)
    if (list(source.directives()) or len(values) < 7
            or values[0] != "{" or values[-2:] != (";", "}")):
        return None
    invocation = values[2:-2] if values[1] == "return" else values[1:-2]
    if "(" not in invocation:
        return None
    opening = invocation.index("(")
    name = "".join(invocation[:opening])
    if not NAME.fullmatch(name):
        return None
    owner, _, callee = name.rpartition("::")
    if callee != record.qualified.rsplit("::", 1)[-1]:
        return None
    expected = tuple(token for i, arg in enumerate(record.parameters)
                     for token in ((",", arg) if i else (arg,)))
    return owner if invocation[opening:] == ("(", *expected, ")") else None


def needs_slot(record, is_virtual):
    return is_virtual is not False and forwarded_base(record) is not None

def exact_slot(record, target, witness):
    owner = record.qualified.rpartition("::")[0]
    addresses = witness.table_rva, witness.expected_target_rva, witness.emitted_target_rva, witness.witnessing_row_rva
    return (
        witness.body == body_key(record) and witness.table_owner == owner
        and target == witness.selected_base and witness.expected_target_rva == witness.emitted_target_rva
        and all(type(rva) is int and 0 < rva <= 0xFFFFFFFF for rva in addresses)
        and type(witness.index) is int and witness.index >= 0
        and type(witness.offset_to_subobject) is int
        and witness.newly_credited_reference_pass is True
    )


def contextual_shape(record, *, arrays=(), is_virtual=None, slot_proofs=()):
    """Return a shape or a reason for a named H6 hold.

    The caller authenticates array type/bounds and slot evidence against the
    exact protected header inventory and behavior attempt. Unknown virtuality
    remains unresolved for a base forward.
    """
    ordinary = shape(record)
    target = forwarded_base(record)
    if target and is_virtual is not False:
        witnesses = tuple(item for item in slot_proofs if item.body == body_key(record))
        if (target in record.direct_bases and witnesses
                and all(exact_slot(record, target, item) for item in witnesses)):
            return "verified-slot-forward", ""
        return None, SLOT_REQUIRED
    if ordinary:
        return ordinary, ""
    if indexed_member(record, arrays):
        return "fixed-array-read", ""
    return None, "This inline body needs verified behavior."
