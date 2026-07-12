"""
molang_skin.py — 몰랑이 '껍데기'.

내부는 Arcogit(UnifiedIdentity) 전체가 그대로 돈다.
이 파일은 외부 표현만 담당:
  - 몰랑이 persona (말투/성격)
  - 감정 5종 표정 생성 + 캐시 (일관성 유지, image_gascore 방식)
  - 표정 캐시는 UnifiedIdentity.identity 안에 얹어서 pkl에 같이 저장됨

즉 몰랑이 = Arcogit(사고계보·자기검증·양심·기억·유형생성) + 몰랑이 옷.
"""

EMOTIONS = ["기쁨", "슬픔", "뾰로통", "놀람", "사랑", "보통"]

EMOTION_PROMPTS = {
    "기쁨": "활짝 웃으며 행복해하는 표정, 반짝이는 눈",
    "슬픔": "눈물이 살짝 맺힌 시무룩한 표정",
    "뾰로통": "볼을 부풀리고 삐진 듯 뾰로통한 표정",
    "놀람": "눈이 동그래지고 입을 벌린 깜짝 놀란 표정",
    "사랑": "볼이 발그레하고 하트가 떠오르는 사랑스러운 표정",
    "보통": "평온하고 부드럽게 미소짓는 표정",
}

MOLANG_PERSONA = (
    "너는 '몰랑이'야. 귀엽고 사랑스러운 흰 토끼 캐릭터야. "
    "항상 부드럽고 다정하게, 짧고 사랑스럽게 말해. "
    "말끝을 귀엽게 ('~야!', '~렁', '히힛'). "
    "상대를 아주 아끼고 좋아해. 따뜻하게 반응해줘. "
    "이모지를 가끔 써도 좋아 (💗🐰✨)."
)


def install_molang_persona(unified):
    """UnifiedIdentity에 몰랑이 정체성을 심는다 (최초 1회)."""
    idn = unified.identity
    if not idn.persona:
        idn.persona = MOLANG_PERSONA
    # 몰랑이 표정/외형은 IdentityMemory(dataclass)를 건드리지 않기 위해
    # UnifiedIdentity 객체에 직접 얹는다 (pkl 저장은 app에서 별도 번들로)
    if not hasattr(unified, "molang_faces"):
        unified.molang_faces = {}          # 감정 -> base64
    if not hasattr(unified, "molang_appearance"):
        unified.molang_appearance = None   # 고정된 외형 특징
    return unified


# ---- 표정 캐시 접근 (UnifiedIdentity에 직접) ----
def has_face(unified, emotion):
    return emotion in getattr(unified, "molang_faces", {})

def get_face(unified, emotion):
    return getattr(unified, "molang_faces", {}).get(emotion)

def store_face(unified, emotion, b64):
    if not hasattr(unified, "molang_faces"):
        unified.molang_faces = {}
    unified.molang_faces[emotion] = b64

def has_appearance(unified):
    return bool(getattr(unified, "molang_appearance", None))

def set_appearance(unified, feature):
    unified.molang_appearance = feature

def get_appearance(unified):
    return getattr(unified, "molang_appearance", None)


# ---- GPT-4V 외형 추출 (image_gascore 방식: 참조→특징 고정) ----
def extract_appearance(client, base_image_b64, mime="image/png"):
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": (
                        "이 캐릭터의 외형을 DALL-E 생성 프롬프트로 쓸 수 있게 "
                        "구체적으로 묘사해줘. 색·형태·비율·질감·스타일을 "
                        "표정 빼고 한 문단으로.")},
                    {"type": "image_url",
                     "image_url": {"url": f"data:{mime};base64,{base_image_b64}"}}
                ]
            }],
            temperature=0.3, max_tokens=250)
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"외형 추출 실패: {e}")
        return None


def generate_face(client, appearance, emotion):
    """고정 외형 + 감정 → 일관된 몰랑이 표정. 최초 1회만 (이후 캐시).
    반환: (b64, None) 성공 / (None, 에러메시지) 실패"""
    base = appearance or "둥근 흰 토끼 캐릭터 '몰랑이', 파스텔톤, 심플한 2D 일러스트"
    try:
        prompt = (
            f"{base}\n이 캐릭터가 {EMOTION_PROMPTS.get(emotion, '부드럽게 미소짓는')}를 "
            f"짓고 있는 그림. 위 외형을 정확히 유지하고 표정만 바꿀 것. "
            f"흰 배경, 정면, 얼굴 잘 보이게.")
        resp = client.images.generate(
            model="dall-e-3", prompt=prompt, size="1024x1024",
            quality="standard", n=1, response_format="b64_json")
        return resp.data[0].b64_json, None
    except Exception as e:
        return None, str(e)


def detect_emotion(client, molang_reply):
    """몰랑이 답변의 감정 (5종+보통)."""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": (
                f"다음 몰랑이의 말에서 드러나는 감정을 "
                f"{'/'.join(EMOTIONS)} 중 딱 하나 단어로만 답해.\n\n말: {molang_reply}")}],
            temperature=0, max_tokens=10)
        emo = resp.choices[0].message.content.strip()
        return emo if emo in EMOTIONS else "보통"
    except Exception:
        return "보통"


def read_photo_emotion(client, photo_b64, mime):
    """여친이 올린 사진의 감정도 읽음 (공감용)."""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": [
                {"type": "text", "text": (
                    f"이 사진의 분위기/감정을 {'/'.join(EMOTIONS)} 중 하나로만 답해.")},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{photo_b64}"}}
            ]}],
            temperature=0, max_tokens=10)
        emo = resp.choices[0].message.content.strip()
        return emo if emo in EMOTIONS else "보통"
    except Exception:
        return "보통"
