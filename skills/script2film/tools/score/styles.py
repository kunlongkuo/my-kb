"""風格設定與和弦工具：音色、速度、調性、角色表。"""

NOTE_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
PC_NAME = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# 小調級數：(相對主音半音, 是否小三和弦)；V 用大三和弦（和聲小調）
MINOR_DEGREES = {"i": (0, True), "iv": (5, True), "V": (7, False),
                 "VI": (8, False), "III": (3, False), "VII": (10, False)}

# 大調七和弦級數（lounge）：(相對主音半音, 和弦性質)
MAJOR_DEGREES = {"I": (0, "maj7"), "ii": (2, "m7"), "iii": (4, "m7"), "IV": (5, "maj7"),
                 "V": (7, "7"), "vi": (9, "m7")}
CHORD_QUALITY = {"": (4, 7), "m": (3, 7), "maj7": (4, 7, 11), "m7": (3, 7, 10), "7": (4, 7, 10)}

ROLES = ("intro", "title", "verse", "body", "warm", "reflect", "pause", "outro")

# 角色 → (級數循環, 聲部, 音量 dB（有旁白）, 音量 dB（無旁白）)
ROLE_TABLE = {
    "intro":   (["i", "i", "iv", "III"], ["pad"], 0, 0),
    "title":   (["VI", "III", "VII"], ["pad", "arp"], -2, -1),
    "verse":   (["i", "VI", "III", "VII"], ["pad", "arp", "bass"], -3, -1),
    "body":    (["i", "VI", "III", "VII", "i", "iv", "V"], ["pad", "arp", "bass"], -4, -1),
    "warm":    (["VI", "III", "VII", "III"], ["pad", "bass", "harp"], -3, -1),
    "reflect": (["iv", "i", "VI", "VII"], ["pad"], -5, -1),
    "pause":   (["i", "VI", "VII"], ["pad", "arp"], 1, 0),
    "outro":   (["III", "VI", "III"], ["pad", "bass", "harp"], 0, 0),
}

# lounge（愛情喜劇、輕爵士）：comp＝Rhodes 切分伴奏、walk＝走路貝斯、swing＝鼓刷 ride 搖擺；大調七和弦
LOUNGE_ROLE_TABLE = {
    "intro":   (["I", "vi", "ii", "V"], ["comp", "walk"], -2, 0),
    "title":   (["IV", "iii", "ii", "V"], ["comp", "walk"], -2, -1),
    "verse":   (["I", "vi", "ii", "V"], ["comp", "walk", "swing"], -3, -1),
    "body":    (["ii", "V", "I", "vi", "ii", "V", "iii", "vi"], ["comp", "walk", "swing"], -4, -1),
    "warm":    (["IV", "iii", "ii", "I"], ["comp", "walk", "swing", "harp"], -3, -1),
    "reflect": (["IV", "I", "ii", "V"], ["comp"], -5, -1),
    "pause":   (["I", "IV"], ["comp", "walk"], 1, 0),
    "outro":   (["ii", "V", "I"], ["comp", "walk", "swing"], 0, 0),
}

STYLES = {
    "devotion": dict(
        programs={"motif": 10, "lead": 0, "harp": 46, "arp": 0, "pad": 49, "bass": 42},
        bpm=(64, 80), target=72, tonic=64, final="III", shaker_roles=()),
    "story": dict(
        programs={"motif": 108, "lead": 12, "harp": 45, "arp": 24, "pad": 48, "bass": 32},
        bpm=(84, 100), target=92, tonic=57, final="i", shaker_roles=("verse", "body")),
    # 電子科幻動作：鋸齒波主旋律、水晶音色、合成器鋪底與低音；drum_roles 的段落有鼓組脈衝，hits 打大鼓＋鈸
    "scifi": dict(
        programs={"motif": 81, "lead": 81, "harp": 98, "arp": 81, "pad": 89, "bass": 38},
        bpm=(120, 140), target=128, tonic=64, final="i", shaker_roles=(), drum_roles=("verse", "body")),
    # 輕爵士 lounge：顫音琴主題、弱音小號長音、爵士吉他分解和弦、Rhodes、低音大提琴；鼓組換 Brush（bank 128 第 40 號）
    "lounge": dict(
        programs={"motif": 11, "lead": 59, "harp": 26, "arp": 4, "pad": 4, "bass": 32},
        bpm=(100, 124), target=112, tonic=65, final="I", shaker_roles=(), mode="major",
        roles=LOUNGE_ROLE_TABLE, drum_kit=40),
    # 史詩管弦 epic（2026-11-19，一支英文喜劇測試短片要 brass-heavy orchestral fanfare；試了五組配器與速度，這組最好）：
    # 法國號主題、小號旋律、慢弦樂分解＋弦樂分解、合唱「啊」鋪底、低音號低音；管弦樂鼓組（bank 128 第 48 號，定音鼓與鈸）在
    # verse／body／title 段；D 小調、128 BPM。試聽意見：大鼓太密（一直咚咚咚）、旋律偏單調，要更大氣就改用 tools/music3
    "epic": dict(
        programs={"motif": 60, "lead": 56, "harp": 49, "arp": 48, "pad": 52, "bass": 58},
        bpm=(120, 136), target=128, tonic=62, final="i", shaker_roles=(), drum_roles=("verse", "body", "title"),
        drum_kit=48),
    # 中東市集 bazaar（做給古代近東題材：story 風格用在另一個系列，兩個聽起來太像）：排笛主題（像蘆笛 ney）、單簧管旋律、西塔琴撥弦分解、
    # 弦樂鋪底、低音大提琴；D 和聲小調（V 大三和弦帶出增二度的中東味）；verse／body 有沙鈴
    "bazaar": dict(
        programs={"motif": 75, "lead": 71, "harp": 46, "arp": 104, "pad": 48, "bass": 32},
        bpm=(90, 106), target=98, tonic=62, final="i", shaker_roles=("verse", "body")),
}
SHAKER = dict(channel=9, bank=128, key=70, vel_on=30, vel_off=48)


def parse_chord(name: str) -> list[int]:
    """'Em' → [4, 7, 11]；'Fmaj7' → [5, 9, 0, 4]；支援 # 與 b、m、maj7、m7、7。"""
    root = NOTE_PC[name[0]]
    rest = name[1:]
    if rest[:1] == "#":
        root, rest = (root + 1) % 12, rest[1:]
    elif rest[:1] == "b":
        root, rest = (root - 1) % 12, rest[1:]
    if rest not in CHORD_QUALITY:
        raise ValueError(f"unsupported chord: {name}")
    return [root] + [(root + i) % 12 for i in CHORD_QUALITY[rest]]


def degree_chord(tonic_pc: int, roman: str, mode: str = "minor") -> str:
    if mode == "major":
        off, quality = MAJOR_DEGREES[roman]
        return PC_NAME[(tonic_pc + off) % 12] + quality
    off, minor = MINOR_DEGREES[roman]
    return PC_NAME[(tonic_pc + off) % 12] + ("m" if minor else "")


def role_table(style: str) -> dict:
    return STYLES[style].get("roles", ROLE_TABLE)
