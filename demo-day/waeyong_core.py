from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
import urllib.request
from collections.abc import Callable
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator
from typing_extensions import TypedDict


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DB_PATH = PROJECT_ROOT / "learning.db"
DEFAULT_IMAGE_DIR = PROJECT_ROOT / "generated"
DEFAULT_WORKFLOW_PROGRESS_MESSAGE = "왜용이 답을 준비하고 있어요."

WORKFLOW_PROGRESS_MESSAGES = {
    "ensure_child_profile": "아이 정보를 확인하고 있어요.",
    "analyze_question": "질문을 분석하고 있어요.",
    "convert_study_subject": "질문을 학습 주제로 정리하고 있어요.",
    "load_prior_learning": "이전 학습 기록을 확인하고 있어요.",
    "generate_parent_coach": "부모를 위한 설명을 만들고 있어요.",
    "decide_activity_feasibility": "어떤 활동이 어울릴지 판단하고 있어요.",
    "generate_activity_guide": "활동 가이드를 만들고 있어요.",
    "decide_image_need": "이미지 카드가 필요한지 살펴보고 있어요.",
    "create_image_card": "이미지 카드를 만들고 있어요.",
    "skip_image_card": "이미지 카드는 생략하고 기록을 정리하고 있어요.",
    "save_learning_record": "학습 기록을 저장하고 있어요.",
}

load_dotenv(PROJECT_ROOT / ".env", override=False)

ProgressCallback = Callable[[str, str], None]
CURRENT_PROGRESS_CALLBACK: ContextVar[ProgressCallback | None] = ContextVar(
    "current_progress_callback",
    default=None,
)


class CuriosityRequest(BaseModel):
    question: str
    target_age: int
    child_interests: list[str] | str | None = None
    explanation_style: str = "짧고 재밌게"
    learner_id: str = ""

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = (value or "").strip()
        if not value:
            raise ValueError("아이 질문은 비어 있을 수 없습니다.")
        return value


class QuestionAnalysis(BaseModel):
    question_type: str = Field(
        description="질문 유형: 과학·자연 / 감정·관계 / 사회·가치 / 민감(죽음·신체·가난 등) / 일상·기타 중 짧게"
    )
    child_intent: str = Field(description="아이 질문 속 호기심·의도")
    parent_need: str = Field(description="부모에게 필요한 도움 유형")
    difficulty_level: str = Field(description="이 연령 기준 설명 난이도: 쉬움|보통|어려움")


class StudySubject(BaseModel):
    title: str = Field(description="학습 주제 제목")
    core_concept: str = Field(description="핵심 개념")
    learning_goal: str = Field(description="학습 목표")
    keywords: list[str] = Field(description="관련 키워드 목록")


class CreativeQuestionGuide(BaseModel):
    observation: str = Field(description="관찰 질문 한 문장")
    imagination: str = Field(description="상상 질문 한 문장")
    comparison: str = Field(description="비교 질문 한 문장")
    inquiry: str = Field(description="탐구 질문 한 문장")


class ParentCoachPack(BaseModel):
    short_answer_30s: str = Field(description="바로 말할 30초 분량 답변")
    story_answer_3min: str = Field(description="조금 더 긴 이야기식 설명")
    play_and_picture_tip: str = Field(description="놀이/그림 활용 팁")
    parent_read_aloud_script: str = Field(description="부모가 바로 읽을 수 있는 스크립트")
    phrases_to_avoid: str = Field(description="피하면 좋은 말")
    say_instead: str = Field(description="대신 할 말")
    follow_up_questions: list[str] = Field(description="되물을 질문 3개")
    creative_question_guide: CreativeQuestionGuide
    next_curiosity_topics: list[str] = Field(description="다음 호기심 주제 3개")


class ActivityFeasibility(BaseModel):
    branch: str = Field(
        description="safe_home_experiment | observation_instead | dialogue_only 중 하나"
    )
    reason: str = Field(description="활동 분기 판단 근거")


class ActivityGuide(BaseModel):
    title: str = Field(description="활동명")
    materials: list[str] = Field(description="준비물")
    steps: list[str] = Field(description="방법 단계")
    safety_note: str = Field(description="안전 문구")
    kind_label: str = Field(description="실험 | 관찰 놀이 | 대화·역할 놀이 등")


class ImageCardPrompt(BaseModel):
    prompt_en: str = Field(description="gpt-image-1.5용 영문 프롬프트")


class QuestionList(BaseModel):
    question_list: list[str] = Field(description="짧은 질문 문자열 목록")


class ImageNeedDecision(BaseModel):
    need_image: bool = Field(description="이미지 카드 필요 여부")
    reason: str = Field(description="판단 근거")


class LearningRecordInput(BaseModel):
    learner_id: str = ""
    question: str
    study_title: str
    core_concept: str
    target_age: int | None = None
    description_excerpt: str = ""
    outcome_summary: str = ""
    question_category: str = ""
    result_payload: str = ""


class CuriosityResult(BaseModel):
    target_age: int
    child_interests: list[str]
    explanation_style: str
    question: str
    question_analysis: QuestionAnalysis
    study_subject: StudySubject
    prior_learning_notes: str = ""
    coach_pack: ParentCoachPack
    activity_feasibility: ActivityFeasibility
    activity_guide: ActivityGuide
    image_need: ImageNeedDecision
    image_card_url: str = ""
    image_card_prompt_en: str = ""
    image_card_prompts: list[str] = Field(default_factory=list)
    image_card_paths: list[str] = Field(default_factory=list)
    related_question_suggestions: list[str] = Field(default_factory=list)
    saved_record_id: int | None = None


class WorkflowState(TypedDict, total=False):
    learner_id: str
    target_age: int
    child_interests: list[str]
    explanation_style: str
    question: str
    question_analysis: QuestionAnalysis
    study_subject: StudySubject
    prior_learning_notes: str
    coach_pack: ParentCoachPack
    activity_feasibility: ActivityFeasibility
    activity_guide: ActivityGuide
    image_card_url: str
    image_card_prompt_en: str
    image_card_prompts: list[str]
    image_card_paths: list[str]
    image_need: ImageNeedDecision
    related_question_suggestions: list[str]
    saved_record_id: int


def normalize_topic_key(title: str) -> str:
    return " ".join((title or "").lower().split())[:200]


def get_activity_branch_label(branch: str) -> str:
    labels = {
        "safe_home_experiment": "집에서 해보는 안전 실험",
        "observation_instead": "관찰 놀이로 이어가기",
        "dialogue_only": "대화·역할 놀이 중심",
    }
    return labels.get(branch, branch)


def get_workflow_progress_message(node_name: str) -> str:
    return WORKFLOW_PROGRESS_MESSAGES.get(node_name, DEFAULT_WORKFLOW_PROGRESS_MESSAGE)


def normalize_request(request: CuriosityRequest) -> CuriosityRequest:
    target_age = max(3, min(8, int(request.target_age)))

    interests = request.child_interests or []
    if isinstance(interests, str):
        interests = [x.strip() for x in interests.replace(",", " ").split() if x.strip()]

    style = (request.explanation_style or "짧고 재밌게").strip() or "짧고 재밌게"
    learner_id = (request.learner_id or "").strip()

    return CuriosityRequest(
        question=request.question,
        target_age=target_age,
        child_interests=list(interests),
        explanation_style=style,
        learner_id=learner_id,
    )


class LearningRepository:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_learning_db()
        self._migrate_learning_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_learning_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_records (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  topic_key TEXT NOT NULL,
                  learner_id TEXT DEFAULT '',
                  question TEXT,
                  study_title TEXT,
                  core_concept TEXT,
                  target_age INTEGER,
                  description_excerpt TEXT,
                  outcome_summary TEXT,
                  result_payload TEXT DEFAULT '',
                  created_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_learning_topic ON learning_records(topic_key)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_learning_learner_topic "
                "ON learning_records(learner_id, topic_key)"
            )
            connection.commit()

    def _migrate_learning_db(self) -> None:
        with self._connect() as connection:
            cur = connection.execute("PRAGMA table_info(learning_records)")
            cols = {row[1] for row in cur.fetchall()}
            if "question_category" not in cols:
                connection.execute(
                    "ALTER TABLE learning_records ADD COLUMN question_category TEXT DEFAULT ''"
                )
                connection.commit()
            if "result_payload" not in cols:
                connection.execute(
                    "ALTER TABLE learning_records ADD COLUMN result_payload TEXT DEFAULT ''"
                )
                connection.commit()
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_learning_learner_category "
                "ON learning_records(learner_id, question_category)"
            )
            connection.commit()

    def list_question_categories(self, learner_id: str = "") -> list[tuple[str, int]]:
        lid = (learner_id or "").strip()
        with self._connect() as connection:
            if lid:
                rows = connection.execute(
                    """
                    SELECT question_category, COUNT(*) FROM learning_records
                    WHERE learner_id = ? AND COALESCE(question_category,'') != ''
                    GROUP BY question_category ORDER BY COUNT(*) DESC
                    """,
                    (lid,),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT question_category, COUNT(*) FROM learning_records
                    WHERE COALESCE(question_category,'') != ''
                    GROUP BY question_category ORDER BY COUNT(*) DESC
                    """
                ).fetchall()
        return [(str(row[0]), int(row[1])) for row in rows]

    def fetch_learning_records(
        self, learner_id: str = "", category: str | None = None, limit: int = 200
    ) -> list[dict[str, Any]]:
        lid = (learner_id or "").strip()
        lim = max(1, min(500, int(limit)))
        cat = (category or "").strip()

        with self._connect() as connection:
            if lid and cat:
                rows = connection.execute(
                    """
                    SELECT id, question_category, question, study_title, created_at, outcome_summary
                    FROM learning_records
                    WHERE learner_id = ? AND question_category = ?
                    ORDER BY id DESC LIMIT ?
                    """,
                    (lid, cat, lim),
                ).fetchall()
            elif lid:
                rows = connection.execute(
                    """
                    SELECT id, question_category, question, study_title, created_at, outcome_summary
                    FROM learning_records
                    WHERE learner_id = ?
                    ORDER BY id DESC LIMIT ?
                    """,
                    (lid, lim),
                ).fetchall()
            elif cat:
                rows = connection.execute(
                    """
                    SELECT id, question_category, question, study_title, created_at, outcome_summary
                    FROM learning_records
                    WHERE question_category = ?
                    ORDER BY id DESC LIMIT ?
                    """,
                    (cat, lim),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT id, question_category, question, study_title, created_at, outcome_summary
                    FROM learning_records
                    ORDER BY id DESC LIMIT ?
                    """,
                    (lim,),
                ).fetchall()
        return [dict(row) for row in rows]

    def fetch_prior_learning_notes(self, topic_key: str, learner_id: str = "") -> str:
        lid = (learner_id or "").strip()
        with self._connect() as connection:
            if lid:
                rows = connection.execute(
                    """
                    SELECT study_title, core_concept, description_excerpt, created_at
                    FROM learning_records
                    WHERE topic_key = ? AND learner_id = ?
                    ORDER BY id DESC LIMIT 5
                    """,
                    (topic_key, lid),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT study_title, core_concept, description_excerpt, created_at
                    FROM learning_records
                    WHERE topic_key = ?
                    ORDER BY id DESC LIMIT 5
                    """,
                    (topic_key,),
                ).fetchall()
        if not rows:
            return ""

        lines: list[str] = []
        for row in rows:
            excerpt_short = str(row["description_excerpt"] or "").replace("\n", " ")[:120]
            lines.append(
                f"- ({row['created_at']}) {row['study_title']} — "
                f"{str(row['core_concept'] or '')[:40]}… 요약: {excerpt_short}"
            )
        return "【이전 호기심 기록】비슷한 주제를 예전에 다뤘을 수 있습니다.\n" + "\n".join(lines)

    def fetch_learning_record_detail(self, record_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, learner_id, question_category, question, study_title, core_concept,
                       target_age, description_excerpt, outcome_summary, result_payload, created_at
                FROM learning_records
                WHERE id = ?
                """,
                (record_id,),
            ).fetchone()
        return dict(row) if row else None

    def save_learning_record(self, record: LearningRecordInput) -> int:
        topic_key = normalize_topic_key(record.study_title)
        with self._connect() as connection:
            cur = connection.execute(
                """
                INSERT INTO learning_records
                (topic_key, learner_id, question, study_title, core_concept, target_age,
                 description_excerpt, outcome_summary, question_category, result_payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    topic_key,
                    record.learner_id,
                    record.question,
                    record.study_title,
                    record.core_concept,
                    record.target_age,
                    record.description_excerpt,
                    record.outcome_summary,
                    record.question_category,
                    record.result_payload,
                ),
            )
            connection.commit()
            return int(cur.lastrowid)


def _image_bytes_extension(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    return ".png"


class WaeyongWorkflow:
    def __init__(
        self,
        repo: LearningRepository | None = None,
        db_path: Path | str = DEFAULT_DB_PATH,
        image_dir: Path | str = DEFAULT_IMAGE_DIR,
        llm_model: str = "openai:gpt-4o-mini",
    ) -> None:
        self.repo = repo or LearningRepository(db_path)
        self.image_dir = Path(image_dir)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.llm = init_chat_model(model=llm_model)
        self.image_tool = self._build_image_tool()
        self.graph = self._build_graph()

    def _build_image_tool(self):
        image_dir = self.image_dir

        @tool
        def generate_education_image_card(prompt_en: str) -> dict:
            """gpt-image-1.5로 교육용 이미지를 받아 디스크에 저장합니다."""
            prompt_en_local = (prompt_en or "").strip()[:4000]
            empty = {"image_card_prompts": [], "image_card_paths": []}
            if not prompt_en_local:
                return empty

            concept_id = hashlib.sha256(prompt_en_local.encode("utf-8")).hexdigest()[:16]

            try:
                client = OpenAI()
                img = client.images.generate(
                    model="gpt-image-1.5",
                    prompt=prompt_en_local,
                    size="1024x1024",
                    quality="low",
                    n=1,
                )
                first = img.data[0]
                b64 = getattr(first, "b64_json", None)
                http_url = getattr(first, "url", None)

                if b64:
                    image_bytes = base64.b64decode(b64)
                    ext = _image_bytes_extension(image_bytes)
                    filename = image_dir / f"image_card_{concept_id}{ext}"
                    filename.write_bytes(image_bytes)
                    return {
                        "image_card_prompts": [prompt_en_local],
                        "image_card_paths": [str(filename)],
                    }

                if http_url:
                    filename = image_dir / f"image_card_{concept_id}.jpg"
                    urllib.request.urlretrieve(http_url, filename)
                    return {
                        "image_card_prompts": [prompt_en_local],
                        "image_card_paths": [str(filename)],
                    }

                return {"image_card_prompts": [prompt_en_local], "image_card_paths": []}
            except Exception as exc:  # pragma: no cover - external API fallback
                print(f"generate_education_image_card tool error: {exc}")
                return {"image_card_prompts": [prompt_en_local], "image_card_paths": []}

        return generate_education_image_card

    def _wrap_node_with_progress(
        self,
        node_name: str,
        node_fn: Callable[[WorkflowState], dict[str, Any]],
    ) -> Callable[[WorkflowState], dict[str, Any]]:
        def wrapped_node(state: WorkflowState) -> dict[str, Any]:
            progress_callback = CURRENT_PROGRESS_CALLBACK.get()
            if callable(progress_callback):
                progress_callback(node_name, get_workflow_progress_message(node_name))
            return node_fn(state)

        return wrapped_node

    def _ensure_child_profile(self, state: WorkflowState) -> dict[str, Any]:
        normalized = normalize_request(
            CuriosityRequest(
                question=state["question"],
                target_age=state.get("target_age", 4),
                child_interests=state.get("child_interests", []),
                explanation_style=state.get("explanation_style", "짧고 재밌게"),
                learner_id=state.get("learner_id", ""),
            )
        )
        return {
            "target_age": normalized.target_age,
            "child_interests": normalized.child_interests,
            "explanation_style": normalized.explanation_style,
            "learner_id": normalized.learner_id,
        }

    def _analyze_question(self, state: WorkflowState) -> dict[str, Any]:
        ta = state.get("target_age", 4)
        interests = state.get("child_interests") or []
        style = state.get("explanation_style") or ""
        response = self.llm.with_structured_output(QuestionAnalysis).invoke(
            f"""
            당신은 부모를 돕는 교육 코치입니다. 아래는 부모가 적어 준 아이의 질문입니다.

            아이 질문:
            {state["question"]}

            아이 나이: {ta}세 (만 나이 기준으로 해석)
            아이가 좋아하는 것(있으면 비유·예시에 반영): {interests}
            부모가 원하는 설명 스타일: {style}

            규칙:
            - 과학 질문으로만 몰아가지 마세요. 감정·사회·민감 주제도 구분합니다.
            - question_type은 반드시 한 줄로: 과학·자연 / 감정·관계 / 사회·가치 / 민감·신체·죽음 등 / 일상·기타 중 가까운 것.
            - 민감 주제는 parent_need에 '조심스러운 대화, 정확한 정보 탐색, 아이 속도 존중' 등을 적습니다.
            """
        )
        return {"question_analysis": response}

    def _convert_study_subject(self, state: WorkflowState) -> dict[str, Any]:
        qa = state["question_analysis"]
        response = self.llm.with_structured_output(StudySubject).invoke(
            f"""
            아이의 질문을 배우기 좋은 학습 주제로 정리합니다. 원 질문과 분석과 동떨어지면 안 됩니다.

            원 질문:
            {state["question"]}

            분석:
            - 유형: {qa.question_type}
            - 아이 의도: {qa.child_intent}
            - 부모에게 필요한 도움: {qa.parent_need}
            - 난이도 감각: {qa.difficulty_level}
            """
        )
        return {"study_subject": response}

    def _load_prior_learning(self, state: WorkflowState) -> dict[str, Any]:
        study = state["study_subject"]
        topic_key = normalize_topic_key(study.title)
        learner_id = (state.get("learner_id") or "").strip()
        notes = self.repo.fetch_prior_learning_notes(topic_key, learner_id)
        return {"prior_learning_notes": notes}

    def _generate_parent_coach(self, state: WorkflowState) -> dict[str, Any]:
        study = state["study_subject"]
        qa = state["question_analysis"]
        ta = state.get("target_age", 4)
        prior = (state.get("prior_learning_notes") or "").strip()
        interests = state.get("child_interests") or []
        style = state.get("explanation_style") or "짧고 재밌게"

        prior_block = ""
        if prior:
            prior_block = (
                f"\n{prior}\n\n예전에 비슷하게 이야기했다면 한두 문장으로 연결한 뒤 오늘 내용으로 이어가세요.\n"
            )

        if ta <= 5:
            age_rules = "【만 5세 이하】전문어 금지 수준. 비유는 일상·좋아하는 것 위주. 문장 짧게."
        elif ta <= 7:
            age_rules = "【만 6~7세】용어는 최소화, 나오면 한 줄 풀어서."
        else:
            age_rules = "【만 8세 전후】조금 더 설명 가능하나 여전히 부모가 읽어 주기 쉬운 말투."

        response = self.llm.with_structured_output(ParentCoachPack).invoke(
            f"""
            당신은 만 3~6세 부모를 위한 호기심 학습 코치입니다. 아이는 직접 타이핑하지 않습니다.

            아이 질문:
            {state["question"]}

            질문 분석:
            - 유형: {qa.question_type}
            - 아이 의도: {qa.child_intent}
            - 부모에게 필요한 것: {qa.parent_need}

            학습 주제: {study.title}
            핵심: {study.core_concept}
            목표: {study.learning_goal}
            키워드: {study.keywords}

            아이 나이: {ta}세 | 좋아하는 것: {interests} | 설명 스타일: {style}
            {prior_block}
            {age_rules}

            출력 규칙:
            - short_answer_30s: 지금 바로 말할 초간단 설명 (2~4문장).
            - story_answer_3min: 조금 더 긴 이야기. 반드시 2~4개의 짧은 문단으로 나누고, 문단 사이를 한 줄 비워 주세요.
            - play_and_picture_tip: 그림·장난감·몸으로 설명하는 방법 한 덩어리.
            - parent_read_aloud_script: 부모가 연속해서 읽을 수 있는 대화형 스크립트.
            - phrases_to_avoid / say_instead: 피할 말과 대신 말 구체적으로.
            - follow_up_questions: 정확히 3개.
            - creative_question_guide: 관찰/상상/비교/탐구 각각 한 문장씩.
            - next_curiosity_topics: 이어서 탐구할 질문·주제 정확히 3개.

            민감·감정 질문이면 과학 실험 대신 공감·안전·경계 존중을 우선하고, 확실치 않은 정보는 단정하지 마세요.
            """
        )
        return {"coach_pack": response}

    def _decide_activity_feasibility(self, state: WorkflowState) -> dict[str, Any]:
        study = state["study_subject"]
        qa = state["question_analysis"]
        response = self.llm.with_structured_output(ActivityFeasibility).invoke(
            f"""
            집에서 할 수 있는 활동 유형을 판단합니다.

            질문 유형: {qa.question_type}
            학습 주제: {study.title}
            핵심 개념: {study.core_concept}

            branch는 반드시 다음 중 하나만:
            - safe_home_experiment
            - observation_instead
            - dialogue_only

            한 줄 reason도 적으세요.
            """
        )
        return {"activity_feasibility": response}

    def _generate_activity_guide(self, state: WorkflowState) -> dict[str, Any]:
        study = state["study_subject"]
        coach = state["coach_pack"]
        fe = state["activity_feasibility"]
        ta = state.get("target_age", 4)

        response = self.llm.with_structured_output(ActivityGuide).invoke(
            f"""
            부모가 아이와 집에서 할 한 가지 활동을 설계합니다.

            분기: {fe.branch}
            이유: {fe.reason}

            주제: {study.title}
            핵심: {study.core_concept}

            코치 요약(참고):
            - 30초 답: {coach.short_answer_30s[:400]}

            규칙:
            - safe_home_experiment: 준비물은 집에서 구하기 쉬운 것. 단계는 3~6개.
            - observation_instead: 산책·하늘 보기·그림 그리기 등 관찰·놀이 중심.
            - dialogue_only: 역할극 대사 예시, 함께 읽을 질문, 안전한 상상 놀이. 실험 강요 금지.

            safety_note에 반드시 보호자 동반·위험 행동 금지를 넣으세요.
            아이 나이 {ta}세에 맞추세요.
            """
        )
        return {"activity_guide": response}

    def _decide_image_need(self, state: WorkflowState) -> dict[str, Any]:
        qa = state["question_analysis"]
        study = state["study_subject"]
        coach = state["coach_pack"]
        fe = state["activity_feasibility"]

        response = self.llm.with_structured_output(ImageNeedDecision).invoke(
            f"""
            아이 질문과 맥락을 보고, 교육용 그림 카드(일러스트)를 이번에 생성할지 판단합니다.

            질문 유형: {qa.question_type}
            학습 주제: {study.title}
            핵심: {study.core_concept}
            활동 분기: {fe.branch} — {fe.reason}
            30초 답 일부: {coach.short_answer_30s[:300]}

            need_image=true:
            자연·과학처럼 눈으로 비유하면 이해가 쉬운 주제, 또는 한 장면 일러스트가 호기심을 붙이는 경우.

            need_image=false 예:
            - 죽음, 폭력, 학대, 가난 등 민감 주제
            - 관계·감정 중심
            - 학습 효과나 안전 측면에서 불필요한 경우

            reason은 한 줄로 명확히 적습니다.
            """
        )
        return {"image_need": response}

    def _skip_image_card(self, state: WorkflowState) -> dict[str, Any]:
        return {
            "image_card_prompt_en": "",
            "image_card_prompts": [],
            "image_card_paths": [],
            "image_card_url": "",
        }

    def _create_image_card(self, state: WorkflowState) -> dict[str, Any]:
        study = state["study_subject"]
        coach = state["coach_pack"]
        ta = state.get("target_age", 4)

        spec = self.llm.with_structured_output(ImageCardPrompt).invoke(
            f"""
            You write ONE English image-generation prompt for OpenAI gpt-image-1.5.

            Topic title: {study.title}
            Core concept: {study.core_concept}
            Visual ideas for a {ta}-year-old:
            {coach.parent_read_aloud_script[:1200]}

            Rules:
            - Single cute friendly scene, bright pastel, simple shapes.
            - No text, letters, or numbers in the image.
            - No violence, horror, or scary realism.
            - Square-friendly learning card composition.
            """
        )
        prompt_en = spec.prompt_en.strip()

        out = self.image_tool.invoke({"prompt_en": prompt_en})
        if not isinstance(out, dict):
            out = {}

        prompts = out.get("image_card_prompts") or ([prompt_en] if prompt_en else [])
        paths = out.get("image_card_paths") or []
        local_path = paths[0] if paths else ""

        return {
            "image_card_prompt_en": prompt_en,
            "image_card_prompts": prompts,
            "image_card_paths": paths,
            "image_card_url": local_path,
        }

    def _save_learning_record(self, state: WorkflowState) -> dict[str, Any]:
        study = state["study_subject"]
        question = state.get("question") or ""
        target_age = state.get("target_age")
        coach = state.get("coach_pack")
        excerpt = (coach.short_answer_30s[:800] if coach else "") or ""
        fe = state.get("activity_feasibility")
        ag = state.get("activity_guide")

        img_need = state.get("image_need")
        image_paths = list(state.get("image_card_paths") or [])
        outcome_summary = "코치패키지·활동"
        if img_need and getattr(img_need, "need_image", False) and image_paths:
            outcome_summary += "·이미지 생성"
        elif img_need and getattr(img_need, "need_image", False):
            outcome_summary += "·이미지 생성 실패"
        elif img_need:
            outcome_summary += f" | 이미지 생략:{getattr(img_need, 'reason', '')[:60]}"
        else:
            outcome_summary += "·이미지 미판단"
        if fe:
            outcome_summary += f" | 활동분기:{fe.branch}"
        if ag:
            outcome_summary += f" | 활동:{ag.title[:40]}"

        qa = state.get("question_analysis")
        question_category = (qa.question_type or "").strip()[:200] if qa else ""
        image_url = str(state.get("image_card_url") or "")
        result_payload = json.dumps(
            {
                "target_age": target_age,
                "child_interests": list(state.get("child_interests") or []),
                "explanation_style": str(state.get("explanation_style") or "짧고 재밌게"),
                "question": question,
                "question_analysis": qa.model_dump() if qa else None,
                "study_subject": study.model_dump(),
                "prior_learning_notes": str(state.get("prior_learning_notes") or ""),
                "coach_pack": coach.model_dump() if coach else None,
                "activity_feasibility": fe.model_dump() if fe else None,
                "activity_guide": ag.model_dump() if ag else None,
                "image_need": img_need.model_dump() if img_need else None,
                "image_card_url": image_url,
                "image_card_prompt_en": str(state.get("image_card_prompt_en") or ""),
                "image_card_prompts": list(state.get("image_card_prompts") or []),
                "image_card_paths": list(state.get("image_card_paths") or []),
            },
            ensure_ascii=False,
        )

        record_id = self.repo.save_learning_record(
            LearningRecordInput(
                learner_id=(state.get("learner_id") or "").strip(),
                question=question,
                study_title=study.title,
                core_concept=study.core_concept,
                target_age=target_age,
                description_excerpt=excerpt,
                outcome_summary=outcome_summary,
                question_category=question_category,
                result_payload=result_payload,
            )
        )

        suggestions: list[str] = []
        if coach and getattr(coach, "next_curiosity_topics", None):
            suggestions = [str(x).strip() for x in coach.next_curiosity_topics if str(x).strip()]
        if len(suggestions) < 3:
            try:
                sug = self.llm.with_structured_output(QuestionList).invoke(
                    f"""
                    같은 맥락에서 아이가 이어서 물을 만한 질문을 3개만.
                    주제: {study.title}
                    핵심: {study.core_concept}
                    """
                )
                for question_text in sug.question_list:
                    question_text = str(question_text).strip()
                    if question_text and question_text not in suggestions:
                        suggestions.append(question_text)
                    if len(suggestions) >= 5:
                        break
            except Exception:  # pragma: no cover - fallback path
                pass

        payload = json.loads(result_payload)
        payload["related_question_suggestions"] = suggestions[:5]
        payload["saved_record_id"] = record_id

        return {
            "related_question_suggestions": suggestions[:5],
            "saved_record_id": record_id,
            "result_payload": json.dumps(payload, ensure_ascii=False),
        }

    @staticmethod
    def _route_image_need(state: WorkflowState) -> str:
        img = state.get("image_need")
        if img is not None and getattr(img, "need_image", False):
            return "create_image_card"
        return "skip_image_card"

    def _build_graph(self):
        graph_builder = StateGraph(WorkflowState)
        graph_builder.add_node(
            "ensure_child_profile",
            self._wrap_node_with_progress("ensure_child_profile", self._ensure_child_profile),
        )
        graph_builder.add_node(
            "analyze_question",
            self._wrap_node_with_progress("analyze_question", self._analyze_question),
        )
        graph_builder.add_node(
            "convert_study_subject",
            self._wrap_node_with_progress("convert_study_subject", self._convert_study_subject),
        )
        graph_builder.add_node(
            "load_prior_learning",
            self._wrap_node_with_progress("load_prior_learning", self._load_prior_learning),
        )
        graph_builder.add_node(
            "generate_parent_coach",
            self._wrap_node_with_progress("generate_parent_coach", self._generate_parent_coach),
        )
        graph_builder.add_node(
            "decide_activity_feasibility",
            self._wrap_node_with_progress(
                "decide_activity_feasibility",
                self._decide_activity_feasibility,
            ),
        )
        graph_builder.add_node(
            "generate_activity_guide",
            self._wrap_node_with_progress("generate_activity_guide", self._generate_activity_guide),
        )
        graph_builder.add_node(
            "decide_image_need",
            self._wrap_node_with_progress("decide_image_need", self._decide_image_need),
        )
        graph_builder.add_node(
            "create_image_card",
            self._wrap_node_with_progress("create_image_card", self._create_image_card),
        )
        graph_builder.add_node(
            "skip_image_card",
            self._wrap_node_with_progress("skip_image_card", self._skip_image_card),
        )
        graph_builder.add_node(
            "save_learning_record",
            self._wrap_node_with_progress("save_learning_record", self._save_learning_record),
        )

        graph_builder.add_edge(START, "ensure_child_profile")
        graph_builder.add_edge("ensure_child_profile", "analyze_question")
        graph_builder.add_edge("analyze_question", "convert_study_subject")
        graph_builder.add_edge("convert_study_subject", "load_prior_learning")
        graph_builder.add_edge("load_prior_learning", "generate_parent_coach")
        graph_builder.add_edge("generate_parent_coach", "decide_activity_feasibility")
        graph_builder.add_edge("decide_activity_feasibility", "generate_activity_guide")
        graph_builder.add_edge("generate_activity_guide", "decide_image_need")
        graph_builder.add_conditional_edges(
            "decide_image_need",
            self._route_image_need,
            {
                "create_image_card": "create_image_card",
                "skip_image_card": "skip_image_card",
            },
        )
        graph_builder.add_edge("create_image_card", "save_learning_record")
        graph_builder.add_edge("skip_image_card", "save_learning_record")
        graph_builder.add_edge("save_learning_record", END)
        return graph_builder.compile()

    def run(
        self,
        request: CuriosityRequest,
        thread_id: str = "streamlit",
        progress_callback: ProgressCallback | None = None,
    ) -> CuriosityResult:
        normalized = normalize_request(request)
        callback_token = None
        if progress_callback is not None:
            callback_token = CURRENT_PROGRESS_CALLBACK.set(progress_callback)
        try:
            result = self.graph.invoke(
                normalized.model_dump(),
                config={"configurable": {"thread_id": thread_id}},
            )
        finally:
            if callback_token is not None:
                CURRENT_PROGRESS_CALLBACK.reset(callback_token)
        return CuriosityResult(
            target_age=int(result["target_age"]),
            child_interests=list(result.get("child_interests") or []),
            explanation_style=str(result.get("explanation_style") or "짧고 재밌게"),
            question=str(result["question"]),
            question_analysis=result["question_analysis"],
            study_subject=result["study_subject"],
            prior_learning_notes=str(result.get("prior_learning_notes") or ""),
            coach_pack=result["coach_pack"],
            activity_feasibility=result["activity_feasibility"],
            activity_guide=result["activity_guide"],
            image_need=result["image_need"],
            image_card_url=str(result.get("image_card_url") or ""),
            image_card_prompt_en=str(result.get("image_card_prompt_en") or ""),
            image_card_prompts=list(result.get("image_card_prompts") or []),
            image_card_paths=list(result.get("image_card_paths") or []),
            related_question_suggestions=list(result.get("related_question_suggestions") or []),
            saved_record_id=result.get("saved_record_id"),
        )


def build_workflow(
    db_path: Path | str = DEFAULT_DB_PATH,
    image_dir: Path | str = DEFAULT_IMAGE_DIR,
    llm_model: str = "openai:gpt-4o-mini",
) -> WaeyongWorkflow:
    return WaeyongWorkflow(db_path=db_path, image_dir=image_dir, llm_model=llm_model)


def run_curiosity(
    request: CuriosityRequest,
    *,
    db_path: Path | str = DEFAULT_DB_PATH,
    image_dir: Path | str = DEFAULT_IMAGE_DIR,
    llm_model: str = "openai:gpt-4o-mini",
    thread_id: str = "streamlit",
) -> CuriosityResult:
    workflow = build_workflow(db_path=db_path, image_dir=image_dir, llm_model=llm_model)
    return workflow.run(request, thread_id=thread_id)
