ILLUSTRATOR_DESCRIPTION = """
(1) PromptBuilderAgent로 페이지(=scene)별 이미지 생성 프롬프트를 최적화하고,
(2) ImageBuilder(또는 generate_images 도구)로 실제 이미지를 생성/저장하는
일러스트 제작 워크플로우 오케스트레이터 에이전트입니다.
모든 단계는 반드시 순차적으로 실행하며(프롬프트 최적화 → 이미지 생성),
생성된 이미지 파일(artifact) 메타데이터만을 반환합니다.
"""