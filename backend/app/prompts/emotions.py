"""32종 감정 템플릿 + 반려동물 종(species)별 오버라이드.

대부분의 라벨/프롬프트는 종에 무관하지만, 일부(인사·꼬리치기·꾹꾹이 등)는
종마다 다른 행동·소리를 갖는다. Emotion.overrides 에 종별로 다른
label_ko/prompt 를 둘 수 있다.
"""
from dataclasses import dataclass, field

# 지원하는 피사체 종류. 반려동물뿐 아니라 식물/인형/사물/음식/캐릭터까지 포괄.
PET_TYPES = (
    "dog", "cat", "rabbit", "hamster", "bird", "monkey",
    "plant", "toy", "object", "food", "character",
    "other",
)
DEFAULT_PET_TYPE = "other"

# 각 피사체의 자연어 디스크립터 (Gemini 프롬프트에 들어감)
SPECIES_DESCRIPTOR = {
    "dog":       "the pet dog",
    "cat":       "the pet cat",
    "rabbit":    "the pet rabbit",
    "hamster":   "the pet hamster (or small rodent)",
    "bird":      "the pet bird",
    "monkey":    "the monkey (or primate)",
    "plant":     "the plant (give it a cute anthropomorphic face — eyes/mouth on the pot or leaves)",
    "toy":       "the stuffed toy/doll (make it lively and animated as if alive)",
    "object":    "the object (anthropomorphize it with a cute face, keep its shape and color)",
    "food":      "the food item (give it a cute face on the surface, keep its appearance)",
    "character": "the character/figure (treat as a living personality)",
    "other":     "the second subject (anthropomorphize cutely if non-living)",
}


@dataclass
class Emotion:
    key: str          # 파일명/식별자
    label_ko: str     # 기본 한글 라벨
    prompt: str       # 기본 영문 행동/표정 묘사
    # 종별 오버라이드: {"cat": {"label_ko": "...", "prompt": "..."}}
    overrides: dict = field(default_factory=dict)

    def resolve(self, pet_type: str) -> tuple[str, str]:
        """주어진 종에 맞는 (label_ko, prompt) 튜플 반환."""
        ov = self.overrides.get(pet_type) or {}
        return ov.get("label_ko", self.label_ko), ov.get("prompt", self.prompt)


# ─────────────────────────── 1) 기본 감정 10종 (전부 종 무관) ──────────────────
BASIC: list[Emotion] = [
    Emotion("hello",    "안녕!",   "waving paw enthusiastically, big bright smile, sparkles around"),
    Emotion("bye",      "잘 가~",  "gentle waving paw, soft warm smile, slight tilt of head"),
    Emotion("thanks",   "고마워",  "hands/paws together in thanks gesture, eyes closed sweetly, small hearts"),
    Emotion("sorry",    "미안해",  "apologetic pose, paws together, downcast eyes, tiny sweat drop"),
    Emotion("congrats", "축하해!", "confetti and party popper, joyful jump, huge grin, sparkles"),
    Emotion("love",     "사랑해",  "big red heart held up, blushing cheeks, dreamy eyes"),
    Emotion("laugh",    "ㅋㅋㅋ",  "rolling on back laughing, mouth wide open, tears of joy"),
    Emotion("cry",      "흑흑..",  "big teary eyes, blue tear streams, quivering lip"),
    Emotion("angry",    "화났어!", "puffed cheeks, steam from ears, eyebrows down, fists/paws clenched"),
    Emotion("shocked",  "헐!!",    "wide open mouth and eyes, exclamation mark above head, leaning back"),
]


# ─────────────────────── 2) 반려동물 일상 12종 (종별 분기 多) ──────────────────
PET_DAILY: list[Emotion] = [
    # 인사
    Emotion(
        "greet", "왔어왔어!",
        "tail wagging energetically, jumping up greeting, hearts around",
        overrides={
            "cat":       {"label_ko": "왔다냥!",   "prompt": "tail upright like a flag, rubbing cheek, soft purring lines"},
            "rabbit":    {"label_ko": "왔다폴짝!", "prompt": "hopping cheerfully, thumping back legs, ears perked"},
            "hamster":   {"label_ko": "왔어왔어~", "prompt": "puffed cheeks, standing on hind legs eagerly"},
            "bird":      {"label_ko": "짹짹왔어!", "prompt": "wings spread flapping, head bobbing, chirp notes"},
            "plant":     {"label_ko": "잎새 인사!", "prompt": "leaves waving like hands, cute face on pot smiling, sparkle"},
            "toy":       {"label_ko": "왔다왔다!", "prompt": "stuffed toy arms raised in greeting, big bright button-eye smile"},
            "object":    {"label_ko": "안녕!",     "prompt": "object with cute face waving (whatever appendage makes sense), sparkles"},
            "food":      {"label_ko": "맛있게 왔어!", "prompt": "food item with cute face, tiny stick arms waving, steam/sparkle"},
            "character": {"label_ko": "왔어왔어!", "prompt": "character striking a greeting pose, signature gesture"},
        },
    ),

    # 소리/울음
    Emotion(
        "bark", "멍멍!",
        "barking enthusiastically, mouth open, sound waves around, paw raised",
        overrides={
            "cat":       {"label_ko": "야옹!",   "prompt": "meowing with eyes closed, mouth open small, dainty sound waves"},
            "rabbit":    {"label_ko": "찍찍!",   "prompt": "small squeak, twitching nose, ears alert"},
            "hamster":   {"label_ko": "찍찍!",   "prompt": "tiny squeak, mouth wide open, cheeks puffed"},
            "bird":      {"label_ko": "짹짹!",   "prompt": "chirping with beak open wide, head tilted up, musical notes"},
            "plant":     {"label_ko": "쑥쑥!",   "prompt": "plant stretching upward, sparkle leaves, growth notes around"},
            "toy":       {"label_ko": "뽀뽀!",   "prompt": "stuffed toy making a cute kiss face, hearts around"},
            "object":    {"label_ko": "띠리링!", "prompt": "object emitting sound/light notes, expressive face"},
            "food":      {"label_ko": "냠냠!",   "prompt": "food with cute mouth open, motion lines suggesting tasty noise"},
            "character": {"label_ko": "와앗!",   "prompt": "character shouting signature catchphrase pose"},
            "other":     {"label_ko": "꺅!",     "prompt": "expressive happy sound, mouth open joyfully"},
        },
    ),

    # 밥/물/돌봄 요청
    Emotion(
        "feed_me", "밥 줘!",
        "holding empty food bowl in mouth, pleading eyes, drool",
        overrides={
            "plant":     {"label_ko": "물 줘!",   "prompt": "plant looking droopy and thirsty, tongue out, water droplet wished"},
            "toy":       {"label_ko": "안아줘!", "prompt": "stuffed toy reaching out arms, big sad-eyes asking for hug"},
            "object":    {"label_ko": "관심 줘!", "prompt": "object with sad face, sparkly pleading eyes"},
            "food":      {"label_ko": "맛봐줘!", "prompt": "food item presenting itself with anticipation"},
            "character": {"label_ko": "도와줘!", "prompt": "character in pleading pose, big puppy eyes"},
        },
    ),

    # 외출/활동
    Emotion(
        "walk", "산책 가자!",
        "leash in mouth, excited bouncy pose, tail wag motion lines",
        overrides={
            "cat":       {"label_ko": "창밖 봐!",   "prompt": "sitting at window watching birds, tail flicking"},
            "rabbit":    {"label_ko": "놀자!",       "prompt": "binkying in the air, ears flying"},
            "hamster":   {"label_ko": "쳇바퀴!",     "prompt": "running on tiny hamster wheel, motion blur"},
            "bird":      {"label_ko": "날자!",       "prompt": "wings spread, ready to fly, taking off"},
            "plant":     {"label_ko": "햇볕 쬐자!",  "prompt": "plant tilting toward sunbeams, leaves wide, sun rays sparkling"},
            "toy":       {"label_ko": "놀러 가자!", "prompt": "stuffed toy holding tiny suitcase or hat, ready for adventure"},
            "object":    {"label_ko": "나가자!",     "prompt": "object with eager face, motion lines as if moving forward"},
            "food":      {"label_ko": "먹으러 가자!","prompt": "food item leaping into action, motion lines, sparkle"},
            "character": {"label_ko": "출동!",       "prompt": "character in heroic running/take-off pose"},
        },
    ),

    Emotion("snack", "간식 주세요", "begging pose, sparkly eyes, paws/hands together pleading"),

    # 멍하니: 이전 "멍..." 라벨이 강아지 소리와 혼동 → "멍하니..." 로 명확화
    Emotion("zone_out", "멍하니...", "blank stare, slightly open mouth, floating dots above head, vacant expression"),

    Emotion("yawn",  "하암~",   "huge yawn, stretching, sleepy half-closed eyes"),
    Emotion("sleep", "쿨쿨",     "curled up sleeping, Z's floating, peaceful face"),
    Emotion("sulk",  "흥! 삐졌어", "turned away with arms/paws crossed, pouting lips, small cloud above"),
    Emotion("mischief", "사고쳤어..", "guilty look, surrounded by scattered torn paper, tiny halo crooked"),
    Emotion("curious",  "이게 뭐야?", "head tilted sideways, big curious eyes, question mark above"),

    # 애정/특기 표현
    Emotion(
        "affection", "꾹꾹이",
        "kneading paws on soft blanket, half-closed blissful eyes",  # 고양이 디폴트
        overrides={
            "dog":       {"label_ko": "배 보여줘", "prompt": "rolling on back, belly up, paws in air, tongue out"},
            "rabbit":    {"label_ko": "발치기",    "prompt": "thumping back legs softly, content expression"},
            "hamster":   {"label_ko": "포실포실",  "prompt": "grooming fluffy fur with tiny paws, eyes content"},
            "bird":      {"label_ko": "깃털 정리", "prompt": "preening feathers carefully with beak, peaceful"},
            "plant":     {"label_ko": "쑥쑥 자라", "prompt": "new leaf sprouting, growth sparkle, plant glowing healthy"},
            "toy":       {"label_ko": "꼬옥",      "prompt": "stuffed toy hugging itself or someone, plush squish lines"},
            "object":    {"label_ko": "반짝반짝",  "prompt": "object polished and shiny, sparkle and shine effects all around"},
            "food":      {"label_ko": "꿀맛!",     "prompt": "food item with closed eyes of bliss, steam and sparkle"},
            "character": {"label_ko": "내 친구!",  "prompt": "character in heart-eyed adoring pose"},
            "other":     {"label_ko": "포근포근",  "prompt": "snuggled into something soft, content expression"},
        },
    ),
]


# ────────────────────── 3) 인물+반려동물 합성/협동 10종 (전부 종 무관) ──────────────
DUO: list[Emotion] = [
    Emotion("on_head",    "내 머리 위!",  "small pet sitting on top of person's head, both smiling cheerfully"),
    Emotion("despair",    "망했다...",    "person and pet slumped together, gloomy aura, dark cloud above"),
    Emotion("fighting",   "파이팅!",      "person and pet both raising fists/paws, sparkles, motivated faces"),
    Emotion("money",      "돈 좋아!",     "person and pet showering in cash, dollar signs in eyes, gleeful"),
    Emotion("tired",      "퇴근하자..",   "person and pet exhausted, droopy eyes, sweat drops, tie loose"),
    Emotion("weekend",    "주말 최고!",   "person and pet leaping joyfully, confetti, big smiles"),
    Emotion("heart_shot", "하트 발사!",   "person and pet shooting heart beams with hands/paws, blushing"),
    Emotion("hug",        "꼬옥 안아",    "person hugging pet tightly, both eyes closed warmly, hearts"),
    Emotion("nope",       "절대 안돼",    "person and pet crossing arms/paws in X shape, stern faces"),
    Emotion("ok",         "오케이!",      "person and pet both giving OK hand/paw sign, winking, sparkle"),
]


ALL_EMOTIONS: list[Emotion] = [*BASIC, *PET_DAILY, *DUO]
assert len(ALL_EMOTIONS) == 32, f"expected 32 emotions, got {len(ALL_EMOTIONS)}"


def get_species_descriptor(pet_type: str) -> str:
    return SPECIES_DESCRIPTOR.get(pet_type, SPECIES_DESCRIPTOR[DEFAULT_PET_TYPE])
