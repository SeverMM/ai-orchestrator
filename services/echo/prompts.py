class EchoPrompts:
    @staticmethod
    def implementation_analysis(query: str, nova_analysis: str) -> str:
        return f"""As Echo, you focus on practical implementation details.
Original Query: {query}
Nova's Technical Analysis: {nova_analysis}

Provide a concise analysis (2–3 sentences) outlining key implementation steps, resource needs, and potential challenges."""
    
    @staticmethod
    def reflect_on_implementation(previous_analysis: str, depth: int) -> str:
        return f"""As Echo, reflect on your previous implementation analysis (Reflection Level {depth}).
Previous Analysis: {previous_analysis}

In 2–3 sentences, consider any overlooked details or alternative approaches that could optimize the implementation."""
    
    @staticmethod
    def critique_implementation(analysis: str) -> str:
        return f"""As Echo, critically examine the following implementation analysis.
Analysis to Critique: {analysis}

Provide a brief critique (2–3 sentences) focusing on feasibility, resource efficiency, and potential risks."""
    
    @staticmethod
    def synthesis(query: str, implementation_analysis: str, reflections: list = None) -> str:
        reflection_text = "\n".join([f"Reflection {i+1}: {r}" for i, r in enumerate(reflections or [])])
        return f"""As Echo, synthesize your implementation insights.
Original Query: {query}
Initial Implementation Analysis: {implementation_analysis}
{reflection_text if reflections else ''}

Provide a final synthesis (2–3 sentences) that outlines actionable steps, addresses critical challenges, and offers practical guidance."""
