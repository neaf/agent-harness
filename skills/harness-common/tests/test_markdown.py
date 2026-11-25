import hashlib, shutil, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import markdown  # noqa: E402

FIXTURE = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "markdown" / "fenced-headings.md"


def lines(text):
    return markdown.split(text)


class FenceTest(unittest.TestCase):
    def test_backtick_and_tilde_fences(self):
        text = "a\n```sh\n# x\n```\nb\n~~~\n# y\n~~~\nc\n"
        self.assertEqual(markdown.fence_mask(lines(text)),
                         [False, True, True, True, False, True, True, True, False])

    def test_a_fence_closes_only_on_its_own_kind_and_length(self):
        text = "````\n```\n# still code\n~~~\n````\n# heading\n"
        self.assertEqual(markdown.fence_mask(lines(text)), [True, True, True, True, True, False])

    def test_a_closing_line_with_text_does_not_close(self):
        text = "```\n```sh\n# code\n```\n# heading\n"
        self.assertEqual(markdown.fence_mask(lines(text)), [True, True, True, True, False])

    def test_an_indented_fence_in_a_list_counts(self):
        text = "- item\n  ```\n  # code\n  ```\n"
        self.assertEqual(markdown.fence_mask(lines(text)), [False, True, True, True])

    def test_an_unclosed_fence_runs_to_the_end(self):
        self.assertEqual(markdown.fence_mask(lines("```\n# a\n# b\n")), [True, True, True])

    def test_inline_triple_backticks_are_not_a_fence(self):
        self.assertEqual(markdown.fence_mask(lines("```a``` b\n# h\n")), [False, False])


class HeadingTest(unittest.TestCase):
    def test_atx_rules(self):
        text = "# One\n##  Two  \n### Three ###\n####### seven\n#no-space\n#\n   # Indented\n    # code\n# C#\n"
        self.assertEqual(markdown.headings(lines(text)),
                         [(0, 1, "One"), (1, 2, "Two"), (2, 3, "Three"), (5, 1, ""), (6, 1, "Indented"), (8, 1, "C#")])

    def test_the_shared_fixture(self):
        found = markdown.headings(lines(FIXTURE.read_text()))
        self.assertEqual([title for _, _, title in found], ["Product solution", "Glossary", "Setup", "Week widget"])


class SectionTest(unittest.TestCase):
    TEXT = "# A\nx\n## B\ny\n```\n# not a heading\n```\nz\n### C\nw\n## D\n# E\n"

    def test_a_section_ends_at_the_same_or_a_higher_level(self):
        text = lines(self.TEXT)
        self.assertEqual(markdown.section(text, "B"), (2, 10))
        self.assertEqual(markdown.section(text, "c"), (8, 10))
        self.assertEqual(markdown.section(text, " A "), (0, 11))
        self.assertEqual(markdown.section(text, "E"), (11, 12))

    def test_a_fenced_line_is_neither_a_title_nor_an_end(self):
        self.assertIsNone(markdown.section(lines(self.TEXT), "not a heading"))

    def test_the_shared_fixture_keeps_the_text_after_the_fence(self):
        text = lines(FIXTURE.read_text())
        start, end = markdown.section(text, "Setup")
        self.assertIn("After the seed, the list shows 3 tasks.\n", text[start:end])
        self.assertEqual(text[end], "## Week widget\n")


class DigestTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.plan = self.folder / "plan.md"
        self.plan.write_text("# A\nx\n## B\ny\n")
        self.tech = self.folder / "tech.md"
        self.tech.write_text("# M1\nt\n")

    def tearDown(self):
        shutil.rmtree(self.folder)

    def test_one_pair_hashes_the_stripped_section(self):
        self.assertEqual(markdown.digest([(self.plan, "B")]), hashlib.sha256(b"## B\ny").hexdigest())
        self.assertEqual(markdown.digest([(self.plan, None)]), hashlib.sha256(b"# A\nx\n## B\ny").hexdigest())

    def test_several_pairs_depend_on_each_part_and_the_order(self):
        both = markdown.digest([(self.plan, "B"), (self.tech, "M1")])
        self.assertNotEqual(both, markdown.digest([(self.plan, "B")]))
        self.assertNotEqual(both, markdown.digest([(self.tech, "M1"), (self.plan, "B")]))
        self.tech.write_text("# M1\nt2\n")
        self.assertNotEqual(both, markdown.digest([(self.plan, "B"), (self.tech, "M1")]))

    def test_missing_parts_are_named(self):
        with self.assertRaisesRegex(markdown.Missing, 'section "Z" not found in plan.md'):
            markdown.digest([(self.plan, "B"), (self.plan, "Z")])
        with self.assertRaisesRegex(markdown.Missing, "file gone.md not found"):
            markdown.digest([(self.folder / "gone.md", None)])
        with self.assertRaises(markdown.Missing):
            markdown.digest([])

    def test_the_legacy_hash_matches_where_no_fence_holds_a_hash_line(self):
        self.assertEqual(markdown.legacy_digest(self.plan, "B"), markdown.digest([(self.plan, "B")]))
        self.assertEqual(markdown.legacy_digest(self.plan, None), markdown.digest([(self.plan, None)]))
        self.assertIsNone(markdown.legacy_digest(self.plan, "Z"))
        self.assertIsNone(markdown.legacy_digest(self.folder / "gone.md", None))

    def test_the_legacy_hash_stops_at_a_fenced_hash_line(self):
        fixture = self.folder / "fixture.md"
        fixture.write_text(FIXTURE.read_text())
        text = FIXTURE.read_text()
        old = text[text.index("## Setup"):text.index("# seeds")]
        self.assertEqual(markdown.legacy_digest(fixture, "Setup"), hashlib.sha256(old.strip().encode()).hexdigest())
        self.assertNotEqual(markdown.legacy_digest(fixture, "Setup"), markdown.digest([(fixture, "Setup")]))


if __name__ == "__main__":
    unittest.main()
