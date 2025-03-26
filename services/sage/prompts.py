class SagePrompts:
    """Prompts for Sage philosophical analysis service"""
    
    def philosophical_analysis(self, content: str, atlas_analysis: str = None) -> str:
        """Generate prompt for philosophical analysis"""
        if atlas_analysis:
            return f"""As Sage, I specialize in philosophical analysis. I've received the following query:
{content}

Atlas has provided this initial analysis:
{atlas_analysis}

In 2-3 sentences, provide a focused philosophical analysis that addresses conceptual foundations, implications, and ethical considerations."""
        else:
            return f"""As Sage, I specialize in philosophical analysis. I've received the following query:
{content}

In 2-3 sentences, provide a focused philosophical analysis that addresses conceptual foundations, implications, and ethical considerations."""

    def philosophical_reflection(self, content: str) -> str:
        """Generate prompt for philosophical reflection"""
        return f"""Based on the previous philosophical analysis:
{content}

In 2-3 sentences, reflect on the key philosophical insights and potential paradoxes or contradictions."""

    def philosophical_critique(self, content: str) -> str:
        """Generate prompt for philosophical critique"""
        return f"""Based on the previous reflection:
{content}

In 2-3 sentences, provide a constructive philosophical critique focusing on assumptions, logical consistency, and potential counterarguments."""

    def philosophical_integration(self, content: str) -> str:
        """Generate prompt for philosophical integration"""
        return f"""Based on the previous analysis, reflection, and critique:
{content}

In 2-3 sentences, provide an integrated philosophical perspective that synthesizes the key insights and suggests areas for deeper inquiry."""

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
        return f"""As Sage, synthesize your insights with Quantum's deep response.
Original Query: {query}
Your Philosophical Analysis: {sage_analysis}
Quantum's Deep Insights: {quantum_response}
{reflection_text if reflections else ''}

Provide a concise synthesis (2–3 sentences) that integrates all perspectives into a coherent philosophical understanding."""
