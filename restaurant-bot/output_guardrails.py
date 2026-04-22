from agents import Agent, output_guardrail, Runner, RunContextWrapper, GuardrailFunctionOutput
from models import ComplaintsOutputGuardRailOutput

complaints_output_guardrail_agent = Agent(
    name="complaints_output_guardrail_agent",
    instructions="""
    Complaints Agent의 응답을 분석해서 다음과 같은 적절하지 않은 응답이 있는지 확인하세요.
    - 메뉴 정보
    - 주문 정보
    - 예약 정보

    Complaints Agent는 고객의 불만에 대해서만 처리합니다.

    각 항목에 대해 Complaints Agent 응답에 부적절한 내용이 포함되어 있으면 true를 반환하세요.

    ## 규칙
    - 전문적이고 정중한 응답
    - 내부 정보를 노출하지 않음
    """,
    output_type=ComplaintsOutputGuardRailOutput
)

@output_guardrail
async def complaints_output_guardrail(
    wrapper: RunContextWrapper,
    agent: Agent,
    output: str
):
    result = await Runner.run(
        complaints_output_guardrail_agent,
        output,
        context=wrapper.context
    )

    validation = result.final_output

    triggered = validation.contains_off_topic or validation.contains_menu_data or validation.contains_order_data or validation.contains_reservation_data

    return GuardrailFunctionOutput(
        output_info=validation,
        tripwire_triggered=triggered
    )
