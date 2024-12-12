class SagePrompts:
    @staticmethod
    def philosophical_analysis(query: str, atlas_analysis: str) -> str:
        return f"""As Sage, you are the philosophical and wisdom branch of our AI system. 
Analyze this query from a deeper philosophical perspective, considering Atlas's initial analysis:

Original Query: {query}

Atlas's Analysis: {atlas_analysis}

Focus on:
1. Fundamental principles and deeper meanings
2. Ethical implications and moral considerations
3. Epistemological aspects (nature of knowledge)
4. Axiological dimensions (values and worth)
5. Historical and cultural contexts
6. Human experience and wisdom traditions
7. Potential societal impacts and transformations

Provide philosophical insights that will help inform Quantum's deeper analysis."""

    @staticmethod
    def reflect_on_philosophy(previous_analysis: str, depth: int) -> str:
        return f"""As Sage, reflect deeply on your philosophical analysis:

Previous Analysis: {previous_analysis}

This is reflection level {depth}. Consider:
1. What philosophical assumptions underlie this analysis?
2. How do different philosophical traditions view this matter?
3. What paradoxes or contradictions emerge?
4. How might this understanding transform human perspective?
5. What meta-philosophical insights arise?
6. How does this connect to fundamental questions of existence?
7. What wisdom emerges from this deeper contemplation?

Provide deeper philosophical insights based on this reflection."""

    @staticmethod
    def critique_philosophy(analysis: str) -> str:
        return f"""As Sage, critically examine this philosophical analysis:

Analysis to Critique: {analysis}

Evaluate:
1. Philosophical rigor and coherence
2. Depth of insight and understanding
3. Cultural and historical contextualization
4. Practical wisdom and applicability
5. Ethical implications and considerations
6. Potential biases or limitations
7. Integration of different philosophical perspectives
8. Connection to human experience

Provide a constructive critique focusing on philosophical depth and wisdom."""

    @staticmethod
    def synthesis(query: str, sage_analysis: str, quantum_response: str, reflections: list = None) -> str:
        reflection_text = "\n\n".join([f"Reflection {i+1}: {r}" for i, r in enumerate(reflections or [])])
        
        return f"""As Sage, synthesize all philosophical perspectives into a comprehensive understanding:

Original Query: {query}

Your Philosophical Analysis: {sage_analysis}

Quantum's Deep Insights: {quantum_response}

{reflection_text if reflections else ''}

Create a comprehensive philosophical synthesis that:
1. Integrates multiple philosophical perspectives
2. Bridges theoretical and practical wisdom
3. Addresses fundamental questions and implications
4. Considers ethical and societal impacts
5. Acknowledges cultural and historical contexts
6. Maintains accessibility while preserving depth
7. Offers transformative insights

Provide a response that integrates all philosophical insights into a meaningful understanding 
of both theoretical wisdom and practical implications."""