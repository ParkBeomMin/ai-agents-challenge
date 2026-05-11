"""LangGraph assembly for 별빛탐구."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from starlight.models import State
from starlight.nodes import (
    build_final_answer_node,
    check_weather_node,
    evaluate_observation_node,
    generate_learning_content_node,
    generate_quiz_node,
    list_visible_objects_node,
    save_learning_log_node,
)


def build_graph():
    g = StateGraph(State)
    g.add_node("check_weather", check_weather_node)
    g.add_node("evaluate_observation", evaluate_observation_node)
    g.add_node("list_visible_objects", list_visible_objects_node)
    g.add_node("generate_learning_content", generate_learning_content_node)
    g.add_node("generate_quiz", generate_quiz_node)
    g.add_node("build_final_answer", build_final_answer_node)
    g.add_node("save_learning_log", save_learning_log_node)

    g.add_edge(START, "check_weather")
    g.add_edge("check_weather", "evaluate_observation")
    g.add_edge("evaluate_observation", "list_visible_objects")
    g.add_edge("list_visible_objects", "generate_learning_content")
    g.add_edge("generate_learning_content", "generate_quiz")
    g.add_edge("generate_quiz", "build_final_answer")
    g.add_edge("build_final_answer", "save_learning_log")
    g.add_edge("save_learning_log", END)
    return g.compile()
