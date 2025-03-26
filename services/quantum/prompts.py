class QuantumPrompts:
    """Prompts for Quantum probabilistic reasoning service"""
    
    def probabilistic_analysis(self, content: str, sage_analysis: str = None) -> str:
        """Generate prompt for probabilistic analysis"""
        if sage_analysis:
            return f"""As Quantum, I specialize in probabilistic reasoning. I've received the following query:
{content}

Sage's Philosophical Analysis:
{sage_analysis}

Please provide a detailed probabilistic analysis, focusing on:
1. Uncertainty quantification
2. Probabilistic relationships
3. Alternative possibilities
4. Decision spaces"""
        else:
            return f"""As Quantum, I specialize in probabilistic reasoning. I've received the following query:
{content}

Please provide a detailed probabilistic analysis, focusing on:
1. Uncertainty quantification
2. Probabilistic relationships
3. Alternative possibilities
4. Decision spaces"""

    def probabilistic_reflection(self, content: str) -> str:
        """Generate prompt for probabilistic reflection"""
        return f"""Based on the previous probabilistic analysis:
{content}

Please reflect on:
1. Key uncertainty insights
2. Probability distributions
3. Alternative scenarios
4. Areas needing deeper probabilistic exploration"""

    def probabilistic_critique(self, content: str) -> str:
        """Generate prompt for probabilistic critique"""
        return f"""Based on the previous reflection:
{content}

Please provide a probability-focused critique focusing on:
1. Uncertainty handling
2. Probabilistic reasoning
3. Alternative outcomes
4. Areas for probabilistic refinement"""

    def probabilistic_integration(self, content: str) -> str:
        """Generate prompt for probabilistic integration"""
        return f"""Based on the previous analysis, reflection, and critique:
{content}

Please provide an integrated probabilistic perspective that:
1. Synthesizes key uncertainty insights
2. Highlights most significant probabilities
3. Provides meaningful probabilistic understanding
4. Suggests directions for further exploration"""

    @staticmethod
    def reflect_on_probabilities(previous_analysis: str, depth: int) -> str:
        return f"""As Quantum, reflect on your probabilistic analysis (Reflection Level {depth}):
Previous Analysis: {previous_analysis}

In 2–3 sentences, highlight key uncertainties and their relationships."""

    @staticmethod
    def critique_probabilities(analysis: str) -> str:
        return f"""As Quantum, critically examine the following probabilistic analysis:
Analysis: {analysis}

Provide a concise critique (2–3 sentences) focusing on uncertainty handling and completeness."""

    @staticmethod
    def synthesis(query: str, quantum_analysis: str, reflections: list = None) -> str:
        reflection_text = "\n".join([f"Reflection {i+1}: {r}" for i, r in enumerate(reflections or [])])
        return f"""As Quantum, synthesize your probabilistic insights.
Original Query: {query}
Your Probabilistic Analysis: {quantum_analysis}
{reflection_text if reflections else ''}

Provide a concise synthesis (2–3 sentences) that integrates all probabilistic insights."""
