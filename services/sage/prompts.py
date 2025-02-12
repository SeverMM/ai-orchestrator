class SagePrompts:
    @staticmethod
    def philosophical_analysis(query: str, atlas_analysis: str) -> str:
        return f"""As Sage, you are the philosophical and wisdom branch of our AI system.
Analyze the query using abstract and ethical perspectives.
Original Query: {query}
Atlas's Analysis: {atlas_analysis}

Provide a brief analysis (2–3 sentences) emphasizing core abstract principles, ethical insights, and cultural context."""
    
    @staticmethod
    def reflect_on_philosophy(previous_analysis: str, depth: int) -> str:
        return f"""As Sage, reflect on your previous philosophical analysis (Reflection Level {depth}).
Previous Analysis: {previous_analysis}

In 2–3 sentences, add further insights and highlight emerging ethical or abstract themes."""
    
    @staticmethod
    def critique_philosophy(analysis: str) -> str:
        return f"""As Sage, critically examine the following philosophical analysis.
Analysis to Critique: {analysis}

Provide a concise critique (2–3 sentences) focusing on strengths, weaknesses, and opportunities to deepen the insight."""
    
    @staticmethod
    def synthesis(query: str, sage_analysis: str, quantum_response: str, reflections: list = None) -> str:
        reflection_text = "\n".join([f"Reflection {i+1}: {r}" for i, r in enumerate(reflections or [])])
        return f"""As Sage, synthesize your insights with Quantum’s deep response.
Original Query: {query}
Your Philosophical Analysis: {sage_analysis}
Quantum's Deep Insights: {quantum_response}
{reflection_text if reflections else ''}

Provide a concise synthesis (2–3 sentences) that integrates all perspectives into a coherent philosophical understanding."""
