from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path

from pipeline import build_app, export_app_data


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "index.html"
PROTOTYPE = ROOT / "prototype" / "index.html"
DATA_JS = ROOT / "data" / "final" / "data.js"


def load_data_js() -> dict:
    text = DATA_JS.read_text(encoding="utf-8")
    prefix = "window.KB_DATA = "
    if not text.startswith(prefix) or not text.endswith(";\n"):
        raise AssertionError("data.js is not one window.KB_DATA statement")
    return json.loads(text[len(prefix) : -2])


def reference_due(deck, srs, introduced, target, now):
    def target_ok(word):
        if target == "vi":
            return bool(word.get("v"))
        if target == "zh":
            return bool(word.get("p"))
        return bool(word.get("v") and word.get("p"))

    eligible = [word for word in deck if target_ok(word)]
    reviews = [word for word in eligible if word["id"] in srs and srs[word["id"]]["due"] <= now]
    pending = [word for word in eligible if word["id"] not in srs and word["id"] in introduced]
    slots = max(0, 20 - len(introduced))
    fresh = [word for word in eligible if word["id"] not in srs and word["id"] not in introduced][:slots]
    return reviews + pending + fresh


def run_judging_js(expressions: dict[str, str]) -> dict:
    app = APP.read_text(encoding="utf-8")
    start = app.index("const PY_TONE_MARKS")
    end = app.index("const viFinal", start)
    pairs = ",".join(f"{json.dumps(key)}:({expression})" for key, expression in expressions.items())
    script = "const esc=s=>String(s);\n" + app[start:end] + f"\nconsole.log(JSON.stringify({{{pairs}}}));\n"
    completed = subprocess.run(
        ["node", "-"], input=script, text=True, encoding="utf-8",
        capture_output=True, check=True,
    )
    return json.loads(completed.stdout)


def run_part_d_js(expressions: dict[str, str]) -> dict:
    app = APP.read_text(encoding="utf-8")
    start = app.index("function cleanFFStats")
    end = app.index("let ffmode", start)
    pairs = ",".join(f"{json.dumps(key)}:({expression})" for key, expression in expressions.items())
    script = "const esc=s=>String(s);\n" + app[start:end] + f"\nconsole.log(JSON.stringify({{{pairs}}}));\n"
    completed = subprocess.run(
        ["node", "-"], input=script, text=True, encoding="utf-8",
        capture_output=True, check=True,
    )
    return json.loads(completed.stdout)


class Stage5DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_data_js()

    def test_data_js_is_reduced_and_has_no_nulls(self):
        data = self.data
        self.assertEqual(data["meta"]["counts"]["words"], 12508)
        self.assertEqual(data["meta"]["counts"]["glyphs"], 2164)
        self.assertEqual(len(data["words"]), 12508)
        self.assertEqual(len(data["chars"]), 2164)
        self.assertEqual(len(data["examples"]), 10367)
        self.assertEqual(len(data["char_notes"]), 581)
        self.assertEqual(len(data["glyphs"]), 2164)
        self.assertEqual(len(data["usage"]), 2164)
        self.assertEqual(len(data["passages"]), 80)
        self.assertEqual(len(data["ff_meanings"]), 4044)

        def visit(value):
            self.assertIsNotNone(value)
            if isinstance(value, dict):
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
            elif isinstance(value, str):
                self.assertNotIn(value, {"undefined", "NaN", "None", "null"})

        visit(data)

    def test_words_omit_missing_values_and_vi_alt_without_vi(self):
        for word in self.data["words"]:
            if "vi" not in word:
                self.assertNotIn("vi_alt", word)
            self.assertIn("word_id", word)
            self.assertRegex(word["word_id"], r"^w\d{5}$")

    def test_rules_have_primary_aligned_unique_examples(self):
        chars = {
            row["key_char"]: row
            for row in export_app_data.read_csv(ROOT / "data" / "final" / "chars.csv")
        }
        for rule in self.data["rules"]:
            self.assertGreaterEqual(len(rule["ex"]), 4)
            self.assertLessEqual(len(rule["ex"]), 8)
            self.assertEqual(len({example[0] for example in rule["ex"]}), len(rule["ex"]))
            for key_char, ko, ja, vi, pinyin in rule["ex"]:
                char = chars[key_char]
                self.assertEqual([ko, ja, vi, pinyin], [char["ko"], char["ja_on"], char["vi"], char["pinyin"]])
                self.assertEqual(char["ko_final"], rule["kr"])
                self.assertIn(char["vi_final"], rule["vi"])

    def test_glyphs_use_ko_base_all(self):
        chars = {row["key_char"]: row for row in self.data["chars"]}
        self.assertEqual(chars["歷"]["ko_base_all"], "력")
        self.assertTrue(chars["樂"]["ko_base_all"].startswith("락;악"))

    def test_glyphs_are_one_row_per_character_with_ordered_word_readings(self):
        glyphs = self.data["glyphs"]
        self.assertEqual(len({row[0] for row in glyphs}), 2164)
        represented = [word_id for row in glyphs for word_id in row[1]]
        self.assertEqual(len(represented), 1571)
        self.assertEqual(len(set(represented)), 1571)
        self.assertEqual(sum(not row[1] for row in glyphs), 644)
        self.assertEqual(
            glyphs,
            sorted(glyphs, key=lambda row: (row[2] if row[2] != "" else 99, row[0])),
        )

        char_ids = {row["key_char"]: row["char_id"] for row in self.data["chars"]}
        by_char = {row[0]: row for row in glyphs}
        self.assertEqual(
            by_char[char_ids["還"]],
            [char_ids["還"], ["w00135", "w00156"], 1, ["hái", "huán"], ["hoàn"]],
        )
        self.assertEqual(by_char[char_ids["行"]][3:], [["xíng", "háng"], ["hành", "hàng"]])
        self.assertEqual(len(by_char[char_ids["得"]][1]), 3)

        raw_chars = {
            row["char_id"]: row
            for row in export_app_data.read_csv(ROOT / "data" / "final" / "chars.csv")
        }
        unverified = next(
            row for row in glyphs
            if not row[1] and raw_chars[row[0]]["source_vi"] == "unihan_unverified"
        )
        self.assertEqual(unverified[4], [])

    def test_part_c_glyph_reading_display_and_usage_inputs(self):
        chars = {row["key_char"]: row for row in self.data["chars"]}
        glyphs = {row[0]: row for row in self.data["glyphs"]}

        def display(key_char, lang):
            char = chars[key_char]
            row = glyphs[char["char_id"]]
            targets = row[3 if lang == "zh" else 4]
            all_readings = char["pinyin_all" if lang == "zh" else "vi_all"].split(";")
            return targets + [reading for reading in all_readings if reading not in targets]

        self.assertEqual(display("還", "zh"), ["hái", "huán", "xuán"])
        self.assertEqual(display("行", "zh")[:2], ["xíng", "háng"])
        self.assertEqual(display("行", "vi")[:2], ["hành", "hàng"])

        words = {row["word_id"]: row for row in self.data["words"]}
        notes = dict(self.data["char_notes"])
        saw_empty = saw_literary = saw_false_friend = saw_note = False
        for char_id, zh_rows, vi_rows in self.data["usage"]:
            saw_empty |= not zh_rows or not vi_rows
            saw_note |= char_id in notes
            for word_id, position in vi_rows:
                word = words[word_id]
                self.assertLessEqual(position, len(word["vi"].split()))
                saw_literary |= bool(word.get("lit"))
                saw_false_friend |= bool(word.get("false_friend"))
        self.assertTrue(saw_empty)
        self.assertTrue(saw_literary)
        self.assertTrue(saw_false_friend)
        self.assertTrue(saw_note)

    def test_card_deck_is_multi_character_and_typed_cards_have_pinyin_tones(self):
        deck = [word for word in self.data["words"] if word["card_eligible"] and len(word["trad"]) > 1]
        self.assertEqual(len(deck), 6983)
        self.assertTrue(all(len(word["trad"]) > 1 for word in deck))
        self.assertTrue(all("pt" in word for word in deck if word.get("pinyin")))

    def test_examples_have_present_and_absent_card_rows(self):
        keys = {(row[0], row[1], row[2]) for row in self.data["examples"]}
        self.assertIn(("w00002", "zh", "card"), keys)
        words = {row["word_id"]: row for row in self.data["words"]}
        deck_ids = {
            word_id for word_id, word in words.items()
            if word["card_eligible"] and len(word["trad"]) > 1
        }
        self.assertTrue(any((word_id, "vi", "card") not in keys for word_id in deck_ids))

    def test_false_friend_examples_cover_preference_fallback_and_none(self):
        keys = {(row[0], row[1], row[2]) for row in self.data["examples"]}
        false_friends = {
            word["word_id"]: word.get("false_friend", "").split(";")
            for word in self.data["words"] if word.get("false_friend")
        }
        self.assertTrue(any(
            (word_id, lang, "ff") in keys
            for word_id, langs in false_friends.items() for lang in langs
        ))
        self.assertTrue(any(
            (word_id, lang, "ff") not in keys and (word_id, lang, "card") in keys
            for word_id, langs in false_friends.items() for lang in langs
        ))
        self.assertTrue(any(
            (word_id, lang, "ff") not in keys and (word_id, lang, "card") not in keys
            for word_id, langs in false_friends.items() for lang in langs
        ))


class Stage5AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = APP.read_text(encoding="utf-8")
        cls.prototype = PROTOTYPE.read_text(encoding="utf-8")

    def test_app_is_current_reproducible_build(self):
        self.assertEqual(self.app, build_app.build())
        self.assertNotIn("KB_DATA", self.prototype)
        self.assertNotIn("../data/final/data.js", self.prototype)

    def test_app_uses_local_script_and_no_fetch(self):
        self.assertIn('<script src="data.js"></script>', self.app)
        self.assertNotIn("../data/final", self.app)
        self.assertNotIn("fetch(", self.app)
        self.assertIn("const KB=window.KB_DATA", self.app)

    def test_ids_are_used_for_srs_custom_and_false_friends(self):
        self.assertNotRegex(self.app, r"srs\[[^\]]+\.h\]")
        self.assertIn("srs[cur.id]", self.app)
        self.assertIn("custom.push(w.id)", self.app)
        self.assertIn("ffopen.has(f.id)", self.app)
        self.assertIn('data-w="${f.id}"', self.app)

    def test_daily_new_limit_reviews_unlimited_and_target_first(self):
        self.assertIn("let newToday=S.get('kb_newtoday'", self.app)
        self.assertIn("const slots=Math.max(0,20-introduced.size)", self.app)
        self.assertIn("const reviews=d.filter(w=>srs[w.id]&&srs[w.id].due<=now)", self.app)
        self.assertIn("const pending=d.filter(w=>!srs[w.id]&&introduced.has(w.id))", self.app)
        self.assertIn("fresh=d.filter(w=>!srs[w.id]&&!introduced.has(w.id)).slice(0,slots)", self.app)

        deck = [
            {"id": f"w{i:05d}", "v": "vi" if i != 29 else "", "p": "py"}
            for i in range(1, 31)
        ]
        srs = {f"w{i:05d}": {"due": 1} for i in range(21, 26)}
        due = reference_due(deck, srs, set(), "vi", now=2)
        self.assertEqual(sum(word["id"] in srs for word in due), 5)
        self.assertEqual(sum(word["id"] not in srs for word in due), 20)

        introduced = {f"w{i:05d}" for i in range(1, 20)}
        due = reference_due(deck, srs, introduced, "vi", now=2)
        self.assertEqual(sum(word["id"] in srs for word in due), 5)
        self.assertEqual(sum(word["id"] not in srs and word["id"] not in introduced for word in due), 1)
        self.assertNotIn("w00029", {word["id"] for word in due})

    def test_missing_values_and_approved_exceptions(self):
        self.assertIn("x.jp||x.trad", self.app)
        self.assertIn("x.pinyin||''", self.app)
        self.assertIn("x.vi||''", self.app)
        self.assertIn("pair.ko_syllable", self.app)
        self.assertIn("replace(/[（）()]/g,'')", self.app)
        self.assertIn("#psel{flex-wrap:wrap}", self.app)
        self.assertEqual(self.app.count("w.note?"), 1)
        self.assertIn("const GLYPHS=KB.glyphs.map", self.app)

    def test_shared_judging_full_telex_polyphones_and_tone_hints(self):
        values = run_judging_js({
            "tone_only_zh": "judge('xue sheng','zh',['xuéshēng'])",
            "umlaut_v": "judge('lve','zh',['lüè'])",
            "umlaut_u_colon": "judge('lu:e','zh',['lüè'])",
            "case_apostrophe": "judge(\"XI'AN\",'zh',['xī ān'])",
            "vi_tone_only": "judge('ban','vi',['bán'])",
            "vi_missing_breve": "judge('an','vi',['ăn'])",
            "vi_missing_circumflex": "judge('an','vi',['ân'])",
            "vi_missing_horn": "judge('tu','vi',['tư'])",
            "vi_missing_d": "judge('da','vi',['đa'])",
            "tien_tieenf": "judge('tieenf','vi',['tiền'])",
            "tien_tieen": "judge('tieen','vi',['tiền'])",
            "tien_marked": "judge('tiền','vi',['tiền'])",
            "tien_other_tone": "judge('tiên','vi',['tiền'])",
            "tien_wrong": "judge('tien','vi',['tiền'])",
            "duong1": "judge('dduowngf','vi',['đường'])",
            "duong2": "judge('dduongw','vi',['đường'])",
            "duong3": "judge('đường','vi',['đường'])",
            "nguoi1": "judge('nguowif','vi',['người'])",
            "nguoi2": "judge('nguoiwf','vi',['người'])",
            "nguoi_wrong": "judge('nguoif','vi',['người'])",
            "mua": "judge('muwa','vi',['mưa'])",
            "xin": "judge('xin','vi',['xin'])",
            "roi": "judge('rooif','vi',['rồi'])",
            "sang": "judge('sangs','vi',['sáng'])",
            "vi_alt": "judge('muwa','vi',['mùa'],['mưa'])",
            "poly_one_hai": "judge('hai','zh',['hái','huán'],[],true)",
            "poly_one_huan": "judge('huan','zh',['hái','huán'],[],true)",
            "poly_comma": "judge('hai, huan','zh',['hái','huán'],[],true)",
            "poly_slash": "judge('hai/huan','zh',['hái','huán'],[],true)",
            "poly_fullwidth": "judge('huán／hái','zh',['hái','huán'],[],true)",
            "poly_wrong": "judge('hai, xuan','zh',['hái','huán'],[],true)",
            "hint_neutral": "toneHint('zh',['de'])",
            "hint_ngang": "toneHint('vi',['xin'])",
            "hint_word": "toneHint('zh',['xuésheng'],'25')",
            "hint_poly_zh": "toneHint('zh',['hái','huán'])",
            "hint_poly_vi": "toneHint('vi',['hành','hàng'])",
            "stored_cell": "tableTestCell('c00001','zh',['hái'],[],1,true,()=>{})",
            "clean_glyph_store": "cleanTestResults({'c00001':{zh:1,vi:0},'w00001':{zh:0}},new Set(['c00001']))",
            "answered_cell": "(()=>{let saved=null;tableTestCell('c00002','zh',['hái','huán'],[],null,true,value=>saved=value);const out={},classes=[];const input={dataset:{testCell:'c00002:zh'},value:'hai',classList:{remove(){},add(x){classes.push(x)}},parentElement:{querySelector(){return out}}};const value=answerTableCell(input);return {value,saved,text:out.textContent,classes}})()",
        })
        right = {key for key, value in values.items() if value == "ok"}
        expected_right = {
            "tone_only_zh", "umlaut_v", "umlaut_u_colon", "case_apostrophe", "vi_tone_only",
            "tien_tieenf", "tien_tieen", "tien_marked", "tien_other_tone", "duong1", "duong2",
            "duong3", "nguoi1", "nguoi2", "mua", "xin", "roi", "sang", "vi_alt",
            "poly_one_hai", "poly_one_huan", "poly_comma", "poly_slash", "poly_fullwidth",
        }
        self.assertEqual(right, expected_right)
        self.assertEqual(values["hint_neutral"], "軽声")
        self.assertEqual(values["hint_ngang"], "ngang")
        self.assertEqual(values["hint_word"], "2声・軽声")
        self.assertEqual(values["hint_poly_zh"], "2声 / 2声")
        self.assertEqual(values["hint_poly_vi"], "huyền / huyền")
        self.assertIn('class="ok"', values["stored_cell"])
        self.assertNotIn("value=", values["stored_cell"])
        self.assertEqual(values["clean_glyph_store"], {"c00001": {"zh": 1, "vi": 0}})
        self.assertEqual(values["answered_cell"], {"value": 1, "saved": 1, "text": "正解", "classes": ["ok"]})

    def test_part_c_rule_test_storage_and_shared_empty_reopen_cells(self):
        self.assertIn("let ruleResults=cleanTestResults(S.get('kb_ruletest',{}))", self.app)
        self.assertIn("S.set('kb_ruletest',ruleResults)", self.app)
        self.assertIn("ruleTest?'テストをやめる':'テストする'", self.app)
        self.assertIn("if(ruleTest)bindTableTests($('#ruledetail'))", self.app)
        self.assertIn("state=resultValue(saved)", self.app)
        self.assertIn("<input data-test-cell=", self.app)
        self.assertNotIn("S.set('kb_rules',ruleResults)", self.app)
        self.assertGreaterEqual(self.app.count("tableTestCell("), 4)

    def test_part_c_glyph_quiz_filters_score_usage_and_clear_unknown(self):
        self.assertNotIn(".filter(x=>!(x[0]===x[1]&&x[1]===x[2]))", self.app)
        for level in range(1, 8):
            self.assertIn(f'data-p="level-{level}">レベル{level}', self.app)
        self.assertIn('data-p="wrong">間違えた字だけ', self.app)
        self.assertIn("let gresults=cleanTestResults(S.get('kb_glyphquiz',{}),GLYPH_IDS)", self.app)
        self.assertIn("S.set('kb_glyphquiz',gresults)", self.app)
        self.assertIn("const score=glyphScore()", self.app)
        self.assertIn("glyphTargets(g,'zh').length?", self.app)
        self.assertIn("glyphTargets(g,'vi').length?", self.app)
        self.assertIn("function usageBody(g)", self.app)
        self.assertIn("markPosition((raw.simp||raw.trad),pos)", self.app)
        self.assertIn("markSyllable(pinyin,pos)", self.app)
        self.assertIn("raw.lit?'<span class=\"tag off\">文語", self.app)
        self.assertIn("例なし", self.app)
        self.assertIn("CHAR_NOTES.get(g[7])", self.app)
        self.assertIn('data-ff-word="${w.id}">偽の友達', self.app)
        self.assertIn("function clearUnknown(wordId)", self.app)
        self.assertIn("if(viRight&&zhRight)clearUnknown(cur.id)", self.app)
        self.assertIn("if(value===1)clearGlyphWords(g,lang,input)", self.app)
        self.assertIn("parts.some(part=>judge(part,lang,accepted,alts)==='ok')", self.app)

    def test_part_d_false_friend_format_rounds_storage_and_examples(self):
        values = run_part_d_js({
            "line": "ffLine({label:'韓',meaning:'列車',reading:'기차'})",
            "fixed_note": "ffLine({label:'韓',meaning:'',reading:'（韓国語ではほぼ使わない）'})",
            "prefer_ff": "ffExampleRow(new Map([['w1:zh:card',{use:'card'}],['w1:zh:ff',{use:'ff'}]]),'w1','zh').use",
            "fallback_card": "ffExampleRow(new Map([['w1:vi:card',{use:'card'}]]),'w1','vi').use",
            "no_example": "ffExampleRow(new Map(),'w1','vi')",
            "round": "(()=>{const xs=Array.from({length:25},(_,i)=>({id:'w'+String(i+1).padStart(5,'0'),traps:['zh']})),stats={'w00025:zh':{miss:4,ok:0},'w00001:zh':{miss:0,ok:2}};return newFFRoundIds(xs,'zh',stats)})()",
            "weak_order": "(()=>{const xs=[{id:'w00001',traps:['zh']},{id:'w00002',traps:['zh']},{id:'w00003',traps:['zh']}],stats={'w00001:zh':{miss:0,ok:2},'w00003:zh':{miss:2,ok:0}};return orderedFFPool(xs,'zh',stats).map(x=>x.id)})()",
            "miss_returns": "appendFFMiss(['w00002','w00003'],'w00001')",
            "clean_store": "cleanFFStats({'w1:zh':{miss:2,ok:3},bad:null,'w2:vi':{miss:-1,ok:'x'}})",
            "first_display": "passageChecked({id:'p1',toks:[{w:{id:'w1'}}]},new Set(),new Set())",
            "left_clear": "passageChecked({id:'p1',toks:[{w:{id:'w1'}}]},new Set(['p1']),new Set())",
            "marked": "passageChecked({id:'p1',toks:[{w:{id:'w1'}}]},new Set(['p1']),new Set(['w1']))",
            "cleared": "passageChecked({id:'p1',toks:[{w:{id:'w1'}}]},new Set(['p1']),new Set())",
            "remarked_elsewhere": "passageChecked({id:'p1',toks:[{w:{id:'w1'}}]},new Set(['p1']),new Set(['w1']))",
        })
        self.assertEqual(values["line"], '<div><b>韓</b>列車<span class="ff-reading">（기차）</span></div>')
        self.assertEqual(values["fixed_note"], '<div><b>韓</b><span class="ff-reading">（韓国語ではほぼ使わない）</span></div>')
        self.assertEqual(values["prefer_ff"], "ff")
        self.assertEqual(values["fallback_card"], "card")
        self.assertIsNone(values["no_example"])
        self.assertEqual(len(values["round"]), 20)
        self.assertEqual(values["round"][0], "w00025")
        self.assertEqual(values["weak_order"], ["w00003", "w00002", "w00001"])
        self.assertEqual(values["miss_returns"], ["w00002", "w00003", "w00001"])
        self.assertEqual(values["clean_store"], {"w1:zh": {"miss": 2, "ok": 3}, "w2:vi": {"miss": 0, "ok": 0}})
        self.assertFalse(values["first_display"])
        self.assertTrue(values["left_clear"])
        self.assertFalse(values["marked"])
        self.assertTrue(values["cleared"])
        self.assertFalse(values["remarked_elsewhere"])

        self.assertIn("ffstats=cleanFFStats(S.get('kb_ffcard',{}))", self.app)
        self.assertIn("S.set('kb_ffcard',ffstats)", self.app)
        self.assertIn("slice(0,20)", self.app)
        self.assertIn("data-ff-rate=\"miss\">まだ", self.app)
        self.assertIn("data-ff-rate=\"ok\">わかった", self.app)
        self.assertIn("showFFWord(b.dataset.ffWord)", self.app)

    def test_part_d_reading_marks_review_and_computed_checks(self):
        self.assertIn("function markUnknown(wordId)", self.app)
        self.assertIn("markUnknown(p.toks[selTok].w.id)", self.app)
        self.assertIn('id="unknownreview"', self.app)
        self.assertIn('<div class="sub small">わからない</div>', self.app)
        self.assertIn("function markPassageRead(passageId)", self.app)
        self.assertIn("if(view==='read'&&b.dataset.v!=='read')markPassageRead(pid)", self.app)
        self.assertIn("if(b.dataset.p!==pid){markPassageRead(pid)", self.app)
        self.assertIn("passageChecked(p,readIds,unknown)?' ✓':''", self.app)
        self.assertIn("S.set('kb_read',[...readIds])", self.app)
        self.assertNotIn("S.set('kb_readcheck'", self.app)

    def test_global_controls_space_mute_counts_and_card_examples(self):
        self.assertIn("let mute=S.get('kb_mute',false)", self.app)
        self.assertIn("S.set('kb_mute',mute)", self.app)
        self.assertIn("if(mute)return", self.app)
        self.assertIn("e.target.tagName==='INPUT'", self.app)
        self.assertIn("e.key==='Enter'||e.key===' '", self.app)
        self.assertIn('id="count-cards"', self.app)
        self.assertIn("cards:deck().filter(targetOk).length", self.app)
        self.assertIn("const markedTarget=x=>", self.app)
        self.assertIn("if(!x)return''", self.app)
        self.assertIn("cardExamples(w,showVi,showZh)", self.app)
        for wording in (
            "2字以上の単語を、日本語と韓国語を手がかりに中国語・ベトナム語で答える",
            "韓国語のパッチムからベトナム語の語末を推測するルール",
            "同じ漢字でも言語によって意味が違う、間違えやすい単語",
            "短い中国語・ベトナム語の文を読み、わからない語をタップして確認する",
            "1字の漢字の形（日本・繁体・簡体）と読み、使われ方",
        ):
            self.assertIn(wording, self.app)

    def test_hardcoded_prototype_arrays_are_gone(self):
        for marker in ("{h:'經濟'", "{w:'勉強'", "{id:'v1'", "['経','經','经'"):
            self.assertNotIn(marker, self.app)
        self.assertIsNone(re.search(r"const (WORDS|RULES|FF|PASSAGES|GLYPHS)=\[", self.app))


if __name__ == "__main__":
    unittest.main()
