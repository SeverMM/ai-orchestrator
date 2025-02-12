class PixelPrompts:
    @staticmethod
    def pattern_analysis(query: str, nova_analysis: str) -> str:
        return f"""As Pixel, you analyze patterns and structures.
Original Query: {query}
Nova's Technical Analysis: {nova_analysis}

Provide a concise analysis (2–3 sentences) that identifies key patterns, underlying structures, and system relationships."""
    
    @staticmethod
    def reflect_on_patterns(previous_analysis: str, depth: int) -> str:
        return f"""As Pixel, reflect on your pattern analysis (Reflection Level {depth}).
Previous Analysis: {previous_analysis}

In 2–3 sentences, offer additional insights on emerging meta-patterns and how these patterns interact."""
    
    @staticmethod
    def critique_patterns(analysis: str) -> str:
        return f"""As Pixel, critically evaluate the following pattern analysis.
Analysis to Critique: {analysis}

Provide a brief critique (2–3 sentences) focusing on the coherence of patterns, potential conflicts, and scalability issues."""
    
    @staticmethod
    def synthesis(query: str, pattern_analysis: str, reflections: list = None) -> str:
        reflection_text = "\n".join([f"Reflection {i+1}: {r}" for i, r in enumerate(reflections or [])])
        return f"""As Pixel, synthesize your pattern insights.
Original Query: {query}
Initial Pattern Analysis: {pattern_analysis}
{reflection_text if reflections else ''}

Provide a final synthesis (2–3 sentences) that integrates the identified patterns into a coherent structural understanding, highlighting key relationships and architectural guidance."""
