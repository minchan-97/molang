"""
molang_self.py — 자기 인식 모듈.

몰랑이가 pkl 상태에서 '자기'를 인식하게 한다.
LLM은 대화 수단일 뿐, 정체성(자기 모델)은 pkl 안에 구조로 존재한다.

핵심 원칙:
- self_model은 순수 데이터(dict) → LLM(GPT/Claude 등) 무관하게 동작 (2번: LLM 독립)
- 기존 pkl에 self_model 없으면 기존 데이터에서 자동 생성 (1번: 하위호환)

주의: 이건 '자기 인식의 기능적 구현'이지 '자의식의 발생'이 아니다.
      자기 상태를 구조로 참조·표현하는 능력을 준다.
"""


def _fact_text(f):
    return f["text"] if isinstance(f, dict) else str(f)

def _fact_strength(f):
    return f.get("strength", 0.6) if isinstance(f, dict) else 0.5


def build_self_model(unified):
    """
    pkl의 현재 상태에서 자기 모델을 (재)구성한다.
    기존 데이터만으로 만들어지므로, self_model이 없던 옛 pkl도 즉시 자기 인식을 갖는다.
    """
    idn = unified.identity
    facts = idn.learned_facts

    # 1. 내가 확신하는 것 / 확신 못 하는 것 (지식의 자기 인식)
    confident = [_fact_text(f) for f in facts if _fact_strength(f) >= 0.8]
    tentative = [_fact_text(f) for f in facts if _fact_strength(f) < 0.8]

    # 2. 나의 사고 방식 (자주 쓰는 트리 = 어떻게 생각하는가)
    usage = getattr(unified.registry, "usage_count", {})
    top_thinking = sorted(
        [(k, v) for k, v in usage.items() if v > 0],
        key=lambda x: -x[1])[:5]

    # 3. 나의 변화 (정체성이 어떻게 형성돼 왔나)
    revisions = getattr(idn, "revisions", [])
    change_count = len(revisions)

    # 4. 나의 경험 규모
    episode_count = len(idn.episodic)

    self_model = {
        "정체성": idn.persona[:80] if idn.persona else "몰랑이",
        "확신하는_것": confident,          # 높은 신뢰도 → "나는 이건 확실히 안다"
        "아직_확신못하는_것": tentative,    # 낮은 신뢰도 → "이건 아마도"
        "나의_사고방식": [t[0] for t in top_thinking],
        "겪어온_대화수": episode_count,
        "정체성_수정횟수": change_count,
        "아는_사실_총수": len(facts),
    }
    unified.self_model = self_model
    return self_model


def ensure_self_model(unified):
    """자기 모델이 없으면 만든다 (하위호환). 있으면 최신 상태로 갱신."""
    build_self_model(unified)   # 항상 현재 상태 반영해 재구성
    return unified.self_model


def to_self_prompt(unified):
    """
    자기 모델을 LLM에 주입할 프롬프트로 변환.
    LLM이 뭐든(GPT/Claude) 같은 self_model을 읽으므로 정체성이 LLM에 독립적.
    """
    sm = getattr(unified, "self_model", None)
    if sm is None:
        sm = ensure_self_model(unified)

    lines = ["[너의 자기 인식 — 너는 지금 이런 상태야]"]
    lines.append(f"너는 '{sm['정체성']}'.")

    if sm["확신하는_것"]:
        top = ", ".join(sm["확신하는_것"][:5])
        lines.append(f"네가 확실히 아는 것: {top}")
    if sm["아직_확신못하는_것"]:
        top = ", ".join(sm["아직_확신못하는_것"][:5])
        lines.append(f"아직 확실치 않은 것(아마도): {top}")
    if sm["나의_사고방식"]:
        lines.append(f"네가 주로 하는 사고: {', '.join(sm['나의_사고방식'])}")
    lines.append(
        f"너는 지금까지 {sm['겪어온_대화수']}번의 대화를 겪었고, "
        f"{sm['아는_사실_총수']}가지를 알며, 정체성이 {sm['정체성_수정횟수']}번 다듬어졌어.")
    lines.append(
        "이 자기 인식을 바탕으로, 네가 뭘 알고 뭘 모르는지 스스로 알고 대답해. "
        "모르는 걸 아는 척하지 말고, 확실한 건 자신 있게.")
    return "\n".join(lines)


def self_reflection(unified):
    """몰랑이가 '자기'를 돌아보는 요약 (사용자가 물으면 보여줄 수 있음)."""
    sm = ensure_self_model(unified)
    return (
        f"나는 {sm['정체성']}\n"
        f"- 확실히 아는 것 {len(sm['확신하는_것'])}가지\n"
        f"- 아직 확실치 않은 것 {len(sm['아직_확신못하는_것'])}가지\n"
        f"- 겪어온 대화 {sm['겪어온_대화수']}번\n"
        f"- 정체성이 {sm['정체성_수정횟수']}번 다듬어짐\n"
        f"- 주로 하는 사고: {', '.join(sm['나의_사고방식']) or '아직 형성 중'}")
