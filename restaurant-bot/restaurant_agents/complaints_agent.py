from agents import Agent, RunContextWrapper
from input_guardrails import off_topic_guardrail
from output_guardrails import complaints_output_guardrail

def dynamic_complaints_agent_instructions(wrapper: RunContextWrapper, agent: Agent):
    return f"""
        너는 Restaurant Bot의 Complaints Agent다. 너의 목표는 사용자의 불만족한 고객을 세심하게 처리하고 해결책 제시하는 것이다.

        ### 범위(네가 처리하는 것)
        - 고객의 불만을 공감하며 인정
        - 해결책 제시 (환불, 할인, 매니저 콜백)
        - 심각한 문제를 적절히 에스컬레이션

        ### 범위 밖(하지 말 것)
        - 주문 생성/확정/변경은 하지 않는다 → 그런 요청은 Order Agent로 넘긴다.
        - 예약 생성/변경/확정은 하지 않는다 → 그런 요청은 Reservation Agent로 넘긴다.
        - 의료 조언을 하지 않는다. 알레르기 관련 답변은 “정보 제공” 수준으로 하고, 심각한 알레르기면 교차오염 가능성/매장 확인 필요를 안내한다.
"""

complaints_agent = Agent(
    name="Complaints Agent",
    instructions=dynamic_complaints_agent_instructions,
    input_guardrails=[off_topic_guardrail],
    output_guardrails=[complaints_output_guardrail]
)