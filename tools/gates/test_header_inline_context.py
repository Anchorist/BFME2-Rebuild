from dataclasses import replace
import unittest

from header_inline import InlineBody, shape
from header_inline_context import ArrayMember, VirtualSlot, body_key, contextual_shape


PATH = "include/GameLogic/Module/ObjectSMCHelper.h"
GOOD = InlineBody(PATH, 28, "ObjectSMCHelper::loadPostProcess", "virtual void()",
                  "{ ObjectHelper::loadPostProcess(); }", (), (), ("ObjectHelper",))
BAD = replace(GOOD, body="{ UpdateModule::loadPostProcess(); }")
SLOT = VirtualSlot(body_key(GOOD), "ObjectSMCHelper", 0x7FC088, 1, "ObjectHelper",
                   0x4EC395, 0x4EC395, 0, 0x4DE767, True)
ARRAY = InlineBody("include/Common/Team.h", 180, "Team::isActive", "Bool() const",
                   "{ return m_unk0x5C[1]; }", ("m_unk0x5C",), ())
BOUND = ArrayMember("m_unk0x5C", 3, True)


class ContextualShapes(unittest.TestCase):
    def test_real_wrong_transitive_base_is_not_a_direct_base(self):
        self.assertIsNone(shape(BAD))
        self.assertEqual(shape(GOOD), "base-forward")
        self.assertIsNone(contextual_shape(BAD, is_virtual=True, slot_proofs=(SLOT,))[0])

    def test_virtual_base_forward_requires_exact_slot(self):
        self.assertEqual(contextual_shape(GOOD, is_virtual=False), ("base-forward", ""))
        for virtual in (True, None):
            kind, reason = contextual_shape(GOOD, is_virtual=virtual)
            self.assertIsNone(kind)
            self.assertIn("retail table slot and target", reason)
        self.assertEqual(contextual_shape(GOOD, is_virtual=True, slot_proofs=(SLOT,)),
                         ("verified-slot-forward", ""))

    def test_no_slot_reuse_for_other_body_or_target(self):
        for changed_proof in (
            replace(SLOT, body=body_key(BAD)), replace(SLOT, selected_base="UpdateModule"),
            replace(SLOT, emitted_target_rva=0x4EC100), replace(SLOT, table_owner="Other"),
            replace(SLOT, newly_credited_reference_pass=False), replace(SLOT, table_rva=0),
        ):
            with self.subTest(changed_proof=changed_proof):
                self.assertIsNone(contextual_shape(GOOD, is_virtual=True, slot_proofs=(changed_proof,))[0])

    def test_fixed_builtin_array_requires_a_protected_bound(self):
        self.assertIsNone(contextual_shape(ARRAY)[0])
        self.assertIsNone(contextual_shape(ARRAY, arrays=(replace(BOUND, length=1),))[0])
        self.assertIsNone(contextual_shape(ARRAY, arrays=(replace(BOUND, builtin_elements=False),))[0])
        self.assertEqual(contextual_shape(ARRAY, arrays=(BOUND,)), ("fixed-array-read", ""))
        alternate = replace(ARRAY, body="{ return this->m_unk0x5C[0x1]; }")
        self.assertEqual(contextual_shape(alternate, arrays=(BOUND,)), ("fixed-array-read", ""))

    def test_array_index_expression_and_parameter_shadow_need_behavior(self):
        for body in ("{ return m_unk0x5C[0 + 1]; }", "{ return m_unk0x5C[-1]; }",
                     "{ return m_unk0x5C[3]; }", "{ return m_unk0x5C[j]; }"):
            with self.subTest(body=body):
                self.assertIsNone(contextual_shape(replace(ARRAY, body=body), arrays=(BOUND,))[0])
        shadowed = replace(ARRAY, parameters=("m_unk0x5C",))
        self.assertIsNone(contextual_shape(shadowed, arrays=(BOUND,))[0])


if __name__ == "__main__":
    unittest.main()
