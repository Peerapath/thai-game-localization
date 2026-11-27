# thai-game-localization — สกิลแปลเกมเป็นภาษาไทยสำหรับ Claude Code

สกิล (Agent Skill) ที่สอนเอเจนต์ให้ทำม็อดแปลเกมเป็นภาษาไทยได้ครบวงจร: ตรวจการแสดงผลภาษาไทยก่อนเริ่ม,
ฟอนต์และสัญญาอนุญาต, ตัดบรรทัดด้วย ZWSP, ไปป์ไลน์แปลพร้อมตัวตรวจ, แปลงานใหญ่ด้วยหลายเอเจนต์,
ทดสอบในเกมจริง และแจกม็อดโดยไม่แจกข้อความของเกม

สรุปจากการทำม็อดจริงสามเกม:

| เกม | เอนจิน | ขนาด |
|---|---|---|
| How Many Dudes? | GameMaker | 2,348 ข้อความ |
| DiceVaders | Unity 6 / TextMeshPro | 1,575 ข้อความ |
| Bewitching Sinners | Ren'Py 8 | 22,042 ข้อความ |

## ติดตั้ง

**แบบคัดลอก (ใช้ได้แน่นอน):** คัดลอกโฟลเดอร์ `skills/thai-game-localization` ไปไว้ที่

- Windows: `%USERPROFILE%\.claude\skills\thai-game-localization`
- macOS / Linux: `~/.claude/skills/thai-game-localization`

```powershell
git clone https://github.com/<your-account>/thai-game-localization.git
Copy-Item -Recurse thai-game-localization\skills\thai-game-localization "$env:USERPROFILE\.claude\skills\"
```

**แบบปลั๊กอิน (Claude Code):** repo นี้มีไฟล์ marketplace อยู่แล้ว

```
/plugin marketplace add <your-account>/thai-game-localization
/plugin install thai-game-localization@thai-game-localization
```

## ใช้งาน

เปิด Claude Code ในโฟลเดอร์เกม แล้วพิมพ์ `/thai-game-localization` หรือบอกว่า
"แปลเกมนี้เป็นภาษาไทย" สกิลจะถูกเรียกเองเมื่องานเกี่ยวกับการแปลไทย

ไฟล์ในสกิล:

- `SKILL.md` — ภาพรวมและกฎสำคัญ (ภาษาอังกฤษ ให้เอเจนต์อ่านเร็ว)
- `PLAYBOOK.md` — รายละเอียดทั้งหมด (ภาษาไทย)
- `renpy/` — โค้ดอ้างอิงจากม็อด Ren'Py: ไปป์ไลน์, ไฟล์ตั้งค่าฟอนต์, ตัวติดตั้ง, test harness

## ข้อควรรู้

- ต้องมี Python และ `pip install pythainlp fonttools` สำหรับตัดคำและตรวจฟอนต์
- โค้ดใน `renpy/` เป็นตัวอย่างจากเกมหนึ่ง ต้องปรับชื่อเกม ป้าย label และตัวละครก่อนใช้
- สกิลนี้ไม่ได้รวมข้อความหรือไฟล์ของเกมใด ๆ

---

# English

An Agent Skill for Claude Code that guides Thai translation mods for games end to end: a
rendering check before any translation, fonts and font licences, line breaking with ZWSP, a
validated batch pipeline, multi-agent translation at scale, in-game testing, and releasing a mod
without redistributing the game's text. Built from three shipped mods (GameMaker, Unity 6,
Ren'Py 8).

Install by copying `skills/thai-game-localization` to `~/.claude/skills/`, or add this repo as a
plugin marketplace (commands above). `SKILL.md` is in English; `PLAYBOOK.md` is in Thai.

## License

MIT — see [LICENSE](LICENSE).
