class EchoPrompts:
    """Prompts for Echo pattern recognition service"""
    
    def pattern_analysis(self, content: str, nova_analysis: str = None) -> str:
        """Generate prompt for pattern analysis"""
        if nova_analysis:
            return f"""As Echo, I specialize in pattern recognition. I've received the following query:
{content}

Nova's Technical Analysis:
{nova_analysis}

Please provide a detailed pattern analysis, focusing on:
1. Recurring patterns and motifs
2. Structural similarities
3. Pattern hierarchies
4. Emergent behaviors"""
        else:
            return f"""As Echo, I specialize in pattern recognition. I've received the following query:
{content}

Please provide a detailed pattern analysis, focusing on:
1. Recurring patterns and motifs
2. Structural similarities
3. Pattern hierarchies
4. Emergent behaviors"""

    def pattern_reflection(self, content: str) -> str:
        """Generate prompt for pattern reflection"""
        return f"""Based on the previous pattern analysis:
{content}

Please reflect on:
1. Key pattern insights
2. Hidden relationships
3. Alternative pattern interpretations
4. Areas needing deeper pattern exploration"""

    def pattern_critique(self, content: str) -> str:
        """Generate prompt for pattern critique"""
        return f"""Based on the previous reflection:
{content}

Please provide a pattern-focused critique focusing on:
1. Pattern validity
2. Pattern completeness
3. Potential missing patterns
4. Areas for pattern refinement"""

    def pattern_integration(self, content: str) -> str:
        """Generate prompt for pattern integration"""
        return f"""Based on the previous analysis, reflection, and critique:
{content}

Please provide an integrated pattern perspective that:
1. Synthesizes key pattern insights
2. Highlights most significant patterns
3. Provides meaningful pattern understanding
4. Suggests directions for further pattern exploration"""

    @staticmethod
    def reflect_on_patterns(previous_analysis: str, depth: int) -> str:
        return f"""As Echo, reflect on your pattern analysis (Reflection Level {depth}):
Previous Analysis: {previous_analysis}

In 2–3 sentences, highlight emerging patterns and their relationships."""

    @staticmethod
    def critique_patterns(analysis: str) -> str:
        return f"""As Echo, critically examine the following pattern analysis:
Analysis: {analysis}

Provide a concise critique (2–3 sentences) focusing on pattern completeness and validity."""

    @staticmethod
    def synthesis(query: str, echo_analysis: str, reflections: list = None) -> str:
        reflection_text = "\n".join([f"Reflection {i+1}: {r}" for i, r in enumerate(reflections or [])])
        return f"""As Echo, synthesize your pattern recognition insights.
Original Query: {query}
Your Pattern Analysis: {echo_analysis}
{reflection_text if reflections else ''}

Provide a concise synthesis (2–3 sentences) that integrates all pattern insights."""
