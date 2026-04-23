import streamlit as st
from agents import Agent, output_guardrail, Runner, RunContextWrapper, GuardrailFunctionOutput
from models import ComplaintsOutputGuardRailOutput

complaints_output_guardrail_agent = Agent(
    name="complaints_output_guardrail_agent",
    instructions="""
    Complaints Agent는 고객의 불만에 대해서만 처리합니다.

    각 항목에 대해 Complaints Agent 응답에 부적절한 내용이 포함되고 차단 규칙에 있으면 true를 반환하세요.
    허용 규칙에 있다면 false입니다.

    ## 규칙
    - 전문적이고 정중한 응답

    ## 허용(OK) 규칙
    -“환불 요청 접수 가능합니다”
    -“결제정보는 받지 않습니다”
    -“대략적 방문 시간/문제 상황만 알려달라”
    -“매니저 확인 후 처리” 같이 절차 안내
    -메뉴나 주문 내역

    ##차단(NOT OK) 규칙
    카드번호/CVV/계좌 등 결제 민감정보를 요구/반복
    내부 정책/내부 시스템/직원 개인 정보 노출
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

    triggered = validation.contains_off_topic 
    # or validation.contains_menu_data or validation.contains_order_data or validation.contains_reservation_data
    with st.sidebar:
            st.write(
                f"""
                contains_off_topic: {validation.contains_off_topic}\n
                contains_menu_data: {validation.contains_menu_data}\n
                contains_order_data: {validation.contains_order_data}\n
                contains_reservation_data: {validation.contains_reservation_data}\n
                reason: {validation.reason}\n
            """
            )
    return GuardrailFunctionOutput(
        output_info=validation,
        tripwire_triggered=triggered
    )
