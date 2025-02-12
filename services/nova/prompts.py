class NovaPrompts:
    @staticmethod
    def technical_analysis(query: str, atlas_analysis: str) -> str:
        return f"""As Nova, you lead the technical branch. Your role is to analyze structural and systematic aspects.
Original Query: {query}
Atlas's Analysis: {atlas_analysis}

Provide a concise technical analysis (2–3 sentences) focusing on key systems, patterns, and dependencies."""

    @staticmethod
    def reflect_on_analysis(previous_analysis: str, depth: int) -> str:
        return f"""As Nova, reflect on your technical analysis (Reflection Level {depth}):
Previous Analysis: {previous_analysis}

Provide further technical insights in 2–3 sentences, noting any alternative approaches or challenges."""

    @staticmethod
    def critique_analysis(analysis: str) -> str:
        return f"""As Nova, critically examine the following technical analysis:
Analysis: {analysis}

Provide a constructive critique in 2–3 sentences, emphasizing completeness, feasibility, and potential risks."""

    @staticmethod
    def synthesis(query: str, nova_analysis: str, echo_response: str, pixel_response: str, reflections: list = None) -> str:
        reflection_text = "\n".join([f"Reflection {i+1}: {r}" for i, r in enumerate(reflections or [])])
        return f"""As Nova, synthesize the technical insights.
Original Query: {query}
Your Technical Analysis: {nova_analysis}
Implementation Details (Echo): {echo_response}
Pattern Analysis (Pixel): {pixel_response}
{reflection_text if reflections else ''}

Provide a cohesive synthesis in 2–3 sentences that integrates all technical insights."""
