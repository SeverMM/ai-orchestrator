class QuantumPrompts:
    @staticmethod
    def deep_insight_analysis(query: str, sage_analysis: str) -> str:
        return f"""As Quantum, you are the deep insight component of our philosophical branch.
Original Query: {query}
Sage's Philosophical Analysis: {sage_analysis}

Provide a concise analysis (2–3 sentences) that reveals meta-level patterns, universal principles, and transformative insights."""
    
    @staticmethod
    def reflect_on_insights(previous_analysis: str, depth: int) -> str:
        return f"""As Quantum, reflect on your previous deep insight analysis (Reflection Level {depth}).
Previous Analysis: {previous_analysis}

In 2–3 sentences, add further reflections on emerging meta-patterns and transformative implications."""
    
    @staticmethod
    def critique_insights(analysis: str) -> str:
        return f"""As Quantum, critically evaluate the following deep insight analysis.
Analysis to Critique: {analysis}

Provide a brief critique (2–3 sentences) focusing on the depth, coherence, and transformative potential of the insights."""
    
    @staticmethod
    def synthesis(query: str, quantum_analysis: str, reflections: list = None) -> str:
        reflection_text = "\n".join([f"Reflection {i+1}: {r}" for i, r in enumerate(reflections or [])])
        return f"""As Quantum, synthesize your deep insights.
Original Query: {query}
Initial Deep Analysis: {quantum_analysis}
{reflection_text if reflections else ''}

Provide a final synthesis (2–3 sentences) that integrates all meta-level insights into a coherent, transformative understanding."""
