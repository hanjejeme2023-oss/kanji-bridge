from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from pipeline.common import _replace_with_retry, hangul_final, normalize_vietnamese, pinyin_numbered_to_marked


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

    def test_atomic_replace_retries_a_short_windows_lock(self) -> None:
        with patch.object(Path, "replace", side_effect=[PermissionError(), Path("done")]) as replace, patch("pipeline.common.time.sleep") as sleep:
            _replace_with_retry(Path("temporary"), Path("target"))
        self.assertEqual(replace.call_count, 2)
        sleep.assert_called_once_with(0.05)


if __name__ == "__main__":
    unittest.main()
