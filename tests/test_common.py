from __future__ import annotations

import unittest

from pipeline.common import hangul_final, normalize_vietnamese, pinyin_numbered_to_marked


class CommonNormalizationTests(unittest.TestCase):
    def test_vietnamese_modern_tone_placement(self) -> None:
        self.assertEqual(normalize_vietnamese("thuỷ"), "thủy")
        self.assertEqual(normalize_vietnamese("thủy"), "thủy")
        self.assertEqual(normalize_vietnamese("hoà"), "hòa")
        self.assertEqual(normalize_vietnamese("khoẻ"), "khỏe")
        for unchanged in ["loạn", "toán", "quý"]:
            self.assertEqual(normalize_vietnamese(unchanged), unchanged)

    def test_hangul_final(self) -> None:
        expected = {
            "학": "ㄱ", "국": "ㄱ", "법": "ㅂ", "일": "ㄹ", "안": "ㄴ",
            "심": "ㅁ", "강": "ㅇ", "가": "",
        }
        for syllable, final in expected.items():
            with self.subTest(syllable=syllable):
                self.assertEqual(hangul_final(syllable), final)

    def test_numbered_pinyin(self) -> None:
        self.assertEqual(pinyin_numbered_to_marked("xue2"), "xué")
        self.assertEqual(pinyin_numbered_to_marked("guo2"), "guó")
        self.assertEqual(pinyin_numbered_to_marked("lü4"), "lǜ")


if __name__ == "__main__":
    unittest.main()
