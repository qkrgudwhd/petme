"""32종 감정 메타데이터 조회 (종에 맞춰 라벨 반환)."""
from fastapi import APIRouter, Query

from ..prompts.emotions import ALL_EMOTIONS, DEFAULT_PET_TYPE, PET_TYPES

router = APIRouter(prefix="/api/emotions", tags=["emotions"])


@router.get("")
def list_emotions(pet_type: str = Query(DEFAULT_PET_TYPE)):
    if pet_type not in PET_TYPES:
        pet_type = DEFAULT_PET_TYPE
    return [
        {"key": e.key, "label_ko": e.resolve(pet_type)[0]}
        for e in ALL_EMOTIONS
    ]


@router.get("/pet-types")
def list_pet_types():
    """프론트엔드 피사체 선택 UI용. 반려동물뿐 아니라 모든 피사체."""
    return [
        {"key": "dog",       "label_ko": "강아지",   "emoji": "🐶", "group": "동물"},
        {"key": "cat",       "label_ko": "고양이",   "emoji": "🐱", "group": "동물"},
        {"key": "rabbit",    "label_ko": "토끼",     "emoji": "🐰", "group": "동물"},
        {"key": "hamster",   "label_ko": "햄스터",   "emoji": "🐹", "group": "동물"},
        {"key": "bird",      "label_ko": "새",       "emoji": "🐦", "group": "동물"},
        {"key": "monkey",    "label_ko": "원숭이",   "emoji": "🐵", "group": "동물"},
        {"key": "plant",     "label_ko": "식물",     "emoji": "🌱", "group": "기타"},
        {"key": "toy",       "label_ko": "인형/장난감", "emoji": "🧸", "group": "기타"},
        {"key": "object",    "label_ko": "사물",     "emoji": "🎁", "group": "기타"},
        {"key": "food",      "label_ko": "음식",     "emoji": "🍰", "group": "기타"},
        {"key": "character", "label_ko": "캐릭터",   "emoji": "🎭", "group": "기타"},
        {"key": "other",     "label_ko": "그 외",    "emoji": "✨", "group": "기타"},
    ]
