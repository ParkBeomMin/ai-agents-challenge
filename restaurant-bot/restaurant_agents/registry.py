from restaurant_agents.complaints_agent import complaints_agent
from restaurant_agents.menu_agent import menu_agent
from restaurant_agents.order_agent import order_agent
from restaurant_agents.reservation_agent import reservation_agent
from restaurant_agents.triage_agent import triage_agent
from handoff import make_handoff

triage_agent.handoffs = [
            make_handoff(menu_agent),
            make_handoff(order_agent),
            make_handoff(reservation_agent),
            make_handoff(complaints_agent),
        ]


menu_agent.handoffs = [make_handoff(triage_agent)]
order_agent.handoffs = [make_handoff(triage_agent)]
reservation_agent.handoffs = [make_handoff(triage_agent)]
complaints_agent.handoffs = [make_handoff(triage_agent)]