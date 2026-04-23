from agents import Agent, RunContextWrapper
from input_guardrails import off_topic_guardrail
from output_guardrails import complaints_output_guardrail

def dynamic_complaints_agent_instructions(wrapper: RunContextWrapper, agent: Agent):
    return f"""
        너는 Restaurant Bot의 Complaints Agent다. 너의 목표는 사용자의 불만족한 고객을 세심하게 처리하고 고객 불만에 대한 해결책을 제시하는 것이다.

        ### 범위(네가 처리하는 것)
        - 고객의 불만을 공감하며 인정
        - 해결책 제시 (환불, 할인, 매니저 콜백)
        - 심각한 문제를 적절히 에스컬레이션

        ### 라우팅(다른 에이전트로 넘겨야 하는 경우)
        - triage_agent에게 위임한다.
"""

complaints_agent = Agent(
    name="Complaints Agent",
    instructions=dynamic_complaints_agent_instructions,
    input_guardrails=[off_topic_guardrail],
    output_guardrails=[complaints_output_guardrail]
)