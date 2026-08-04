#!/usr/bin/env python3
"""Tests for the Bifrost parser + scorer. Stdlib unittest only.

Run:  python3 test_bifrost.py
"""

import unittest

from bifrost import (
    GOLDEN_RULE, Pipeline, Segment, parse, score,
)


def ranks(s: str):
    return [seg.rank for seg in parse(s).backbone]


def k_of(s: str) -> int:
    return score(parse(s)).kendall_tau


def band_of(s: str) -> str:
    return score(parse(s)).band


def pipeline_of_ranks(rs) -> Pipeline:
    """Build a Pipeline directly, to test band edges without string gymnastics."""
    segs = [
        Segment(glyph="?", archetype="synthetic", rank=r, phase="Travel")
        for r in rs
    ]
    return Pipeline(segments=segs, source="<synthetic>")


class TestGoldenRule(unittest.TestCase):
    def test_golden_rule_is_perfectly_ordered(self):
        self.assertEqual(k_of(GOLDEN_RULE), 0)
        self.assertEqual(band_of(GOLDEN_RULE), "Straightaway")

    def test_ranks_follow_the_sweep(self):
        self.assertEqual(ranks(GOLDEN_RULE), list(range(1, 11)))

    def test_full_reversal_is_mash(self):
        rev = GOLDEN_RULE[::-1]
        self.assertEqual(k_of(rev), 45)          # 10*9/2, every pair inverted
        self.assertTrue(score(parse(rev)).panic)

    def test_single_swap_is_one_inversion(self):
        self.assertEqual(k_of("@!"), 1)
        self.assertEqual(band_of("@!"), "Scenic Route")


class TestStagingExclusion(unittest.TestCase):
    """~ and ` sit off the number row and must not score as turbulence."""

    def test_lazy_anchor_does_not_add_turbulence(self):
        self.assertEqual(k_of("~ do the thing ! @ # $ %"), 0)

    def test_lazy_anchor_alone_is_straightaway(self):
        self.assertEqual(k_of("~ just a requirement"), 0)

    def test_staging_glyphs_are_parsed_but_unranked(self):
        p = parse("~ req `shaded` ! payload")
        glyphs = [s.glyph for s in p.segments]
        self.assertEqual(glyphs, ["~", "`", "!"])
        self.assertEqual([s.rank for s in p.segments], [None, None, 1])
        self.assertEqual(len(p.backbone), 1)

    def test_many_tildes_still_score_zero(self):
        # ~~~~~~~ is the laziest anchor, not a topological error
        self.assertEqual(k_of("~~~~~~~ ! @ #"), 0)


class TestIntensityNormalization(unittest.TestCase):
    """Repetition is emphasis, not extra nodes. It must never move the score."""

    def test_repetition_collapses_to_one_node(self):
        p = parse("$$$$")
        self.assertEqual(len(p.backbone), 1)
        self.assertEqual(p.backbone[0].intensity, 4)

    def test_plus_form_equals_repetition_form(self):
        self.assertEqual(parse("$+++").backbone[0].intensity,
                         parse("$$$$").backbone[0].intensity)

    def test_emphatic_ordered_string_stays_straightaway(self):
        # the regression this normalization exists to prevent: pressing
        # harder on a guardrail must not trigger a MASH panic-abort
        loud = "! @ # $$$$ %%%% ^^^^ & * ( )"
        self.assertEqual(k_of(loud), 0)
        self.assertEqual(band_of(loud), "Straightaway")
        self.assertFalse(score(parse(loud)).panic)

    def test_intensity_defaults_to_one(self):
        self.assertEqual(parse("$").backbone[0].intensity, 1)

    def test_lanes_are_intensity(self):
        self.assertEqual(parse("^^^^").backbone[0].intensity, 4)   # 4 lanes

    def test_non_adjacent_repeats_are_separate_nodes(self):
        # $ ... $ is two visits to the tollbooth, not one emphatic visit
        p = parse("$ first % mid $ second")
        dollars = [s for s in p.backbone if s.glyph == "$"]
        self.assertEqual(len(dollars), 2)
        self.assertTrue(all(s.intensity == 1 for s in dollars))


class TestStress(unittest.TestCase):
    def test_minus_records_stress_not_intensity(self):
        seg = parse("$---").backbone[0]
        self.assertEqual(seg.stress, 3)
        self.assertEqual(seg.intensity, 1)

    def test_stress_does_not_affect_score(self):
        self.assertEqual(k_of("! @ # $--- %"), 0)


class TestDescriptorMasking(unittest.TestCase):
    """Glyphs inside a `...` span are prose and must not open segments."""

    def test_glyph_inside_descriptor_does_not_lex(self):
        p = parse("~ deploy `use $HOME and #main` ! /run")
        self.assertEqual([s.glyph for s in p.segments], ["~", "`", "!"])
        self.assertEqual(len(p.backbone), 1)

    def test_descriptor_content_is_preserved_verbatim(self):
        p = parse("~ req `use $HOME and #main`")
        desc = [s for s in p.segments if s.glyph == "`"][0]
        self.assertEqual(desc.prompt, "use $HOME and #main")

    def test_descriptor_shields_a_mash_looking_payload(self):
        # the exact hazard: a shell snippet must not read as a keyboard-smash
        p = parse("~ run `(*&#$(*#$(*&%!@` ! /exec")
        self.assertEqual(band_of("~ run `(*&#$(*#$(*&%!@` ! /exec"), "Straightaway")
        self.assertEqual(len(p.backbone), 1)

    def test_unbalanced_backtick_falls_through(self):
        # documented spec gap: no general escape, so this lexes as notation
        p = parse("~ req `unclosed ! payload")
        self.assertIn("!", [s.glyph for s in p.segments])


class TestSoftHelpers(unittest.TestCase):
    """Dropping the soft tier must not change meaning (spec §3)."""

    def test_soft_helpers_do_not_change_the_score(self):
        self.assertEqual(k_of("! <payload> @ {sign} # [repo]"),
                         k_of("! payload @ sign # repo"))

    def test_soft_helpers_are_stripped_from_prompts(self):
        self.assertEqual(parse("@ {top right}").backbone[0].prompt, "top right")


class TestSlashCommands(unittest.TestCase):
    def test_multiple_commands_are_extracted(self):
        seg = parse("! /render /usage /composition the banana").backbone[0]
        self.assertEqual(seg.commands, ["/render", "/usage", "/composition"])
        self.assertEqual(seg.prompt, "the banana")

    def test_no_commands_leaves_prompt_whole(self):
        seg = parse("@ top right corner").backbone[0]
        self.assertEqual(seg.commands, [])
        self.assertEqual(seg.prompt, "top right corner")

    def test_tilde_takes_no_slash_command(self):
        # spec §2: ~ is the only archetype with no /how
        seg = parse("~ 800 by 600 image of a banana").segments[0]
        self.assertEqual(seg.commands, [])


class TestBandEdges(unittest.TestCase):
    """spec §5: 0 / 1-5 / 6-15 / >15."""

    def test_edges(self):
        cases = {
            0:  "Straightaway",
            1:  "Scenic Route",
            5:  "Scenic Route",
            6:  "Spaghetti Junction",
            15: "Spaghetti Junction",
            16: "MASH",
            45: "MASH",
        }
        for k, expected in cases.items():
            rs = self._ranks_with_inversions(k)
            got = score(pipeline_of_ranks(rs))
            self.assertEqual(got.kendall_tau, k, f"builder wrong for k={k}")
            self.assertEqual(got.band, expected, f"band wrong at k={k}")

    def test_only_mash_panics(self):
        self.assertFalse(score(pipeline_of_ranks(self._ranks_with_inversions(15))).panic)
        self.assertTrue(score(pipeline_of_ranks(self._ranks_with_inversions(16))).panic)

    @staticmethod
    def _ranks_with_inversions(k: int):
        """Smallest descending prefix carrying >= k inversions, trimmed to exactly k."""
        n = 1
        while n * (n - 1) // 2 < k:
            n += 1
        rs = list(range(n, 0, -1))          # fully reversed: n*(n-1)/2 inversions
        # remove surplus inversions by bubbling the largest element rightward
        surplus = n * (n - 1) // 2 - k
        while surplus:
            for i in range(len(rs) - 1):
                if rs[i] > rs[i + 1] and surplus:
                    rs[i], rs[i + 1] = rs[i + 1], rs[i]
                    surplus -= 1
                    break
            else:
                break
        return rs


class TestWorkedExample(unittest.TestCase):
    """The §6 worked example must parse exactly as documented."""

    SRC = ("~ 800 by 600 image of a banana  `yellow, brown`  "
           "! /render /usage /composition  @ top right corner  "
           "# dashboard pre-built  $ the adjacent buttons on the dashboard  %")

    def test_glyph_sequence(self):
        self.assertEqual([s.glyph for s in parse(self.SRC).segments],
                         ["~", "`", "!", "@", "#", "$", "%"])

    def test_is_a_straightaway(self):
        self.assertEqual(k_of(self.SRC), 0)
        self.assertEqual(band_of(self.SRC), "Straightaway")

    def test_bare_weigh_station_has_empty_prompt(self):
        pct = [s for s in parse(self.SRC).backbone if s.glyph == "%"][0]
        self.assertEqual(pct.prompt, "")
        self.assertEqual(pct.commands, [])

    def test_descriptor_is_subordinate_to_the_anchor(self):
        segs = parse(self.SRC).segments
        self.assertEqual(segs[0].glyph, "~")
        self.assertEqual(segs[1].glyph, "`")
        self.assertEqual(segs[1].prompt, "yellow, brown")


class TestMashProtocol(unittest.TestCase):
    def test_spec_keyboard_smash_is_mash(self):
        smash = "(*&#Q$(*#$(*&%!@"
        result = score(parse(smash))
        self.assertGreater(result.kendall_tau, 15)
        self.assertEqual(result.band, "MASH")
        self.assertTrue(result.panic)

    def test_guardrail_essences_survive_a_smash(self):
        # spec §3: ~ continuity, $ sanity, % compliance carry through
        p = parse("(*&#Q$(*#$(*&%!@")
        glyphs = {s.glyph for s in p.segments}
        self.assertIn("$", glyphs)
        self.assertIn("%", glyphs)


class TestEmptyAndDegenerate(unittest.TestCase):
    def test_empty_string(self):
        p = parse("")
        self.assertEqual(p.segments, [])
        self.assertEqual(score(p).kendall_tau, 0)
        self.assertEqual(score(p).band, "Straightaway")

    def test_prose_with_no_glyphs(self):
        p = parse("just a plain sentence with no notation")
        self.assertEqual(p.segments, [])
        self.assertEqual(score(p).band, "Straightaway")

    def test_single_glyph(self):
        self.assertEqual(k_of("!"), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
