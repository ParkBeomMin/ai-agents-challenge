import unittest

from starlight.graph import build_graph


class BuildGraphStructureTest(unittest.TestCase):
    def test_graph_starts_with_check_weather_without_validate_input(self) -> None:
        graph = build_graph().get_graph()

        self.assertNotIn("validate_input", graph.nodes)
        start_targets = {edge.target for edge in graph.edges if edge.source == "__start__"}
        self.assertEqual(start_targets, {"check_weather"})


if __name__ == "__main__":
    unittest.main()
