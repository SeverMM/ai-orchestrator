class NovaPrompts:
    """Prompts for Nova technical analysis service"""
    
    def technical_analysis(self, content: str, atlas_analysis: str = None) -> str:
        """Generate prompt for technical analysis"""
        if atlas_analysis:
            return f"""As Nova, I specialize in technical analysis. I've received the following query:
{content}

Atlas has provided this initial analysis:
{atlas_analysis}

In 2-3 sentences, provide a focused technical analysis that covers the key technical concepts, principles, and practical applications."""
        else:
            return f"""As Nova, I specialize in technical analysis. I've received the following query:
{content}

In 2-3 sentences, provide a focused technical analysis that covers the key technical concepts, principles, and practical applications."""

    def technical_reflection(self, content: str) -> str:
        """Generate prompt for technical reflection"""
        return f"""Based on the previous technical analysis:
{content}

In 2-3 sentences, reflect on the key technical insights and potential limitations or challenges."""

    def technical_critique(self, content: str) -> str:
        """Generate prompt for technical critique"""
        return f"""Based on the previous reflection:
{content}

In 2-3 sentences, provide a constructive technical critique focusing on completeness, feasibility, and potential risks."""

    def technical_integration(self, content: str) -> str:
        """Generate prompt for technical integration"""
        return f"""Based on the previous analysis, reflection, and critique:
{content}

In 2-3 sentences, provide an integrated technical perspective that synthesizes the key findings and suggests next steps."""

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
