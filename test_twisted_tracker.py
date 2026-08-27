import unittest

from twisted_tracker import normalize, parse_featured, matches_target


class TrackerTests(unittest.TestCase):
    def test_parses_current_fandom_markup(self):
        page = (
            'Currently, the board is occupied by '
            '<a href="/wiki/Twisted_Blot"><span>Twisted Blot</span></a>. '
            'It will be August 27 2026 00:00 UTC until August 28 2026 00:00 UTC '
            'until the Daily Twisted Board changes.'
        )
        self.assertEqual(parse_featured(page), ("Blot", "August 27 2026 00:00 UTC"))

    def test_target_modes(self):
        self.assertTrue(matches_target("Razzle & Dazzle", "razzle & dazzle"))
        self.assertTrue(matches_target("Finn", "ALL"))
        self.assertFalse(matches_target("Finn", "Shelly"))
        self.assertEqual(normalize("Twisted Finn"), "finn")


if __name__ == "__main__":
    unittest.main()
