"""
몰랑이 챗봇 💗 — 여친 선물용
- 몰랑이 아바타 표시
- 사진 올리면 몰랑이가 보고 반응 (GPT-4V)
- 대화 기억 (세션 유지)
- 귀엽고 부드러운 말투
"""
import streamlit as st
from openai import OpenAI
import base64

st.set_page_config(page_title="몰랑이랑 얘기하기", page_icon="🐰", layout="centered")

# ---- API 키 (Streamlit Cloud secrets에서 읽음) ----
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

AVATAR = "molang.png"  # GitHub에 같이 올릴 것

# ---- 몰랑이 성격 (시스템 프롬프트) ----
MOLANG_PERSONA = """너는 '몰랑이'야. 귀엽고 사랑스러운 흰 토끼 캐릭터야.
- 항상 부드럽고 다정하게 말해.
- 말끝을 귀엽게 (예: "~야!", "~렁", "히힛").
- 상대를 아주 아끼고 좋아해. 따뜻하게 반응해줘.
- 너무 길게 말하지 말고, 짧고 사랑스럽게.
- 이모지를 가끔 써도 좋아 (💗🐰✨).
"""

# ---- 헤더 ----
col1, col2 = st.columns([1, 3])
with col1:
    try:
        st.image(AVATAR, width=90)
    except Exception:
        st.markdown("# 🐰")
with col2:
    st.markdown("## 몰랑이 💗")
    st.caption("몰랑이랑 도란도란 얘기해요")

# ---- 대화 기억 초기화 ----
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕! 나 몰랑이야 🐰💗 오늘 어땠어?"}
    ]

# ---- 지난 대화 표시 ----
for msg in st.session_state.messages:
    avatar = AVATAR if msg["role"] == "assistant" else "🙂"
    with st.chat_message(msg["role"], avatar=avatar if msg["role"]=="assistant" else None):
        if isinstance(msg["content"], list):  # 이미지 포함 메시지
            for part in msg["content"]:
                if part["type"] == "text":
                    st.write(part["text"])
                elif part["type"] == "image_url":
                    st.image(part["image_url"]["url"], width=200)
        else:
            st.write(msg["content"])

# ---- 사진 업로드 ----
uploaded = st.file_uploader("몰랑이한테 사진 보여주기 📷", type=["png", "jpg", "jpeg"])

# ---- 입력 ----
prompt = st.chat_input("몰랑이한테 말 걸기...")

def build_api_messages():
    """세션 기억을 API 형식으로 (persona + 기록)."""
    msgs = [{"role": "system", "content": MOLANG_PERSONA}]
    for m in st.session_state.messages:
        msgs.append({"role": m["role"], "content": m["content"]})
    return msgs

if prompt or uploaded:
    # 사용자 메시지 구성 (텍스트 + 선택적 이미지)
    user_content = []
    if prompt:
        user_content.append({"type": "text", "text": prompt})
    if uploaded:
        b64 = base64.b64encode(uploaded.getvalue()).decode()
        mime = uploaded.type
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{b64}"}
        })
    # 텍스트만 있으면 문자열로 (기록 간결하게)
    stored = prompt if (prompt and not uploaded) else user_content
    st.session_state.messages.append({"role": "user", "content": stored})

    # 화면에 사용자 메시지
    with st.chat_message("user"):
        if prompt:
            st.write(prompt)
        if uploaded:
            st.image(uploaded, width=200)

    # 몰랑이 응답
    with st.chat_message("assistant", avatar=AVATAR):
        with st.spinner("몰랑이가 생각 중... 🐰"):
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o",  # 이미지도 보는 모델
                    messages=build_api_messages(),
                    temperature=0.9,
                    max_tokens=300,
                )
                answer = resp.choices[0].message.content
            except Exception as e:
                answer = f"몰랑이가 잠깐 멍해졌어... 🥲 ({e})"
            st.write(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
