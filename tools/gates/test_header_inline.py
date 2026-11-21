from dataclasses import replace
import unittest

from git_objects import ObjectError
from header_inline import InlineBody, classify_changed, missing_behavior, shape

RECORD = InlineBody("include/Derived.h", 10, "Game::Derived::update",
                    "member(int)", "{ return this->value; }", ("value",), ("arg",), ("Base", "Game::Parent"))


class Shapes(unittest.TestCase):
    def check(self, value, expected):
        self.assertEqual(shape(replace(RECORD, body=value)), expected, value)

    def test_direct_member_read(self):
        self.check("{ return value; }", "member-read")
        self.check("{ return this->value; }", "member-read")
        self.check("{ /* why */ return this->value; }", "member-read")

    def test_direct_member_write(self):
        self.check("{ value = arg; }", "member-write")
        self.check("{ this->value = arg; }", "member-write")

    def test_base_forward(self):
        self.check("{ Base::update(arg); }", "base-forward")
        self.check("{ return Game::Parent::update(arg); }", "base-forward")

    def test_another_field_or_receiver_requires_evidence(self):
        self.check("{ return other; }", None)
        self.check("{ return another.value; }", None)
        self.check("{ return getValue(); }", None)

    def test_value_transformation_is_not_forwarding(self):
        self.check("{ Base::update(arg + 1); }", None)
        self.check("{ Unrelated::update(arg); }", None)
        self.check("{ Base::different(arg); }", None)
        self.check("{ value += arg; }", None)

    def test_macros_initializers_and_empty_body_are_not_certified(self):
        self.check("{\n#ifdef FOO\nreturn value;\n#endif\n}", None)
        self.check("{}", None)
        self.assertIsNone(shape(replace(RECORD, initializers="Base(Compute())")))

    def test_comment_and_layout_churn_do_not_request_evidence(self):
        change = replace(RECORD, line=12, body="{ return /* explanation */ this->value; }")
        self.assertEqual(classify_changed([RECORD], [change], complete=True), ([], []))

    def test_exact_body_is_required_in_evidence(self):
        change = replace(RECORD, body="{ return other; }")
        _, required = classify_changed([RECORD], [change], complete=True)
        result = missing_behavior(required, [replace(required[0], body_sha256="0" * 64)])
        self.assertEqual((result[0].rule, result[0].line), ("H6", 10))
        self.assertEqual(missing_behavior(required, required), [])

    def test_parameter_can_shadow_a_member(self):
        changed = replace(RECORD, body="{ return value; }", parameters=("value",))
        self.assertIsNone(shape(changed))
        explicit = replace(changed, body="{ return this->value; }")
        self.assertEqual(shape(explicit), "member-read")

    def test_changed_member_binding_requires_reclassification(self):
        before = replace(RECORD, body="{ return value; }")
        _, required = classify_changed([before], [replace(before, fields=())], complete=True)
        self.assertEqual(len(required), 1)

    def test_incomplete_inventory_cannot_pass(self):
        with self.assertRaisesRegex(ObjectError, "H6"):
            classify_changed([], [], complete=False)


if __name__ == "__main__":
    unittest.main()
