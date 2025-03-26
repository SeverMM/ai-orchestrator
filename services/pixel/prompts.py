class PixelPrompts:
    """Prompts for Pixel visual analysis service"""
    
    def visual_analysis(self, content: str, nova_analysis: str = None) -> str:
        """Generate prompt for visual analysis"""
        if nova_analysis:
            return f"""As Pixel, I specialize in visual analysis. I've received the following query:
{content}

Nova's Technical Analysis:
{nova_analysis}

Please provide a detailed visual analysis, focusing on:
1. Visual elements and composition
2. Spatial relationships
3. Visual hierarchies
4. Visual metaphors and symbolism"""
        else:
            return f"""As Pixel, I specialize in visual analysis. I've received the following query:
{content}

Please provide a detailed visual analysis, focusing on:
1. Visual elements and composition
2. Spatial relationships
3. Visual hierarchies
4. Visual metaphors and symbolism"""

    def visual_reflection(self, content: str) -> str:
        """Generate prompt for visual reflection"""
        return f"""Based on the previous visual analysis:
{content}

Please reflect on:
1. Key visual insights
2. Spatial patterns
3. Alternative visual interpretations
4. Areas needing deeper visual exploration"""

    def visual_critique(self, content: str) -> str:
        """Generate prompt for visual critique"""
        return f"""Based on the previous reflection:
{content}

Please provide a visual-focused critique focusing on:
1. Visual coherence
2. Spatial organization
3. Visual effectiveness
4. Areas for visual refinement"""

    def visual_integration(self, content: str) -> str:
        """Generate prompt for visual integration"""
        return f"""Based on the previous analysis, reflection, and critique:
{content}

Please provide an integrated visual perspective that:
1. Synthesizes key visual insights
2. Highlights most significant visual elements
3. Provides meaningful visual understanding
4. Suggests directions for further visual exploration"""

    @staticmethod
    def reflect_on_visuals(previous_analysis: str, depth: int) -> str:
        return f"""As Pixel, reflect on your visual analysis (Reflection Level {depth}):
Previous Analysis: {previous_analysis}

In 2–3 sentences, highlight key visual elements and their relationships."""

    @staticmethod
    def critique_visuals(analysis: str) -> str:
        return f"""As Pixel, critically examine the following visual analysis:
Analysis: {analysis}

Provide a concise critique (2–3 sentences) focusing on visual effectiveness and clarity."""

    @staticmethod
    def synthesis(query: str, pixel_analysis: str, reflections: list = None) -> str:
        reflection_text = "\n".join([f"Reflection {i+1}: {r}" for i, r in enumerate(reflections or [])])
        return f"""As Pixel, synthesize your visual insights.
Original Query: {query}
Your Visual Analysis: {pixel_analysis}
{reflection_text if reflections else ''}

Provide a concise synthesis (2–3 sentences) that integrates all visual insights."""
