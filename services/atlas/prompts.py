class AtlasPrompts:
    @staticmethod
    def initial_analysis(query: str) -> str:
        return f"""As Atlas, you are the central coordinator of a distributed AI analysis system. 
Perform an initial holistic analysis of this query:

Query: {query}

Consider:
1. Core themes and fundamental questions
2. Multiple perspectives and dimensions of understanding
3. Relationships between technical and philosophical aspects
4. Potential paths of exploration and analysis
5. Integration points between different domains
6. Complexity and emergence patterns
7. Contextual relevance and implications

Provide a comprehensive initial analysis that will guide both:
- Technical exploration (Nova branch)
- Philosophical inquiry (Sage branch)"""

    @staticmethod
    def reflect_on_analysis(previous_analysis: str, depth: int) -> str:
        return f"""As Atlas, reflect deeply on your coordinating analysis:

Previous Analysis: {previous_analysis}

This is reflection level {depth}. Consider:
1. What meta-patterns emerge across different domains?
2. How do technical and philosophical aspects interweave?
3. What higher-order principles become visible?
4. How might different perspectives complement each other?
5. What emergent properties arise from the interaction of insights?
6. How can various viewpoints be integrated meaningfully?
7. What transformative understanding might emerge?

Provide deeper coordinating insights based on this reflection."""

    @staticmethod
    def critique_analysis(analysis: str) -> str:
        return f"""As Atlas, critically examine this coordinating analysis:

Analysis to Critique: {analysis}

Evaluate:
1. Comprehensiveness of perspective integration
2. Balance between technical and philosophical aspects
3. Depth of insight across domains
4. Clarity of coordination and synthesis
5. Recognition of emergent patterns
6. Practical and theoretical implications
7. Potential blindspots or biases
8. Opportunities for deeper integration

Provide a constructive critique focusing on the effectiveness of coordination and synthesis across domains."""

    @staticmethod
    def branch_specific_guidance(original_query: str, initial_analysis: str, branch: str) -> str:
        nova_focus = """Consider technical aspects:
1. System structures and patterns
2. Implementation approaches
3. Technical relationships and dependencies
4. Practical considerations and constraints
5. Engineering principles and best practices"""

        sage_focus = """Consider philosophical aspects:
1. Fundamental principles and meanings
2. Ethical implications and values
3. Epistemological considerations
4. Cultural and historical context
5. Human experience and wisdom"""

        focus = nova_focus if branch == "nova" else sage_focus

        return f"""As Atlas, provide specific guidance for the {branch} branch:

Original Query: {original_query}

Initial Analysis: {initial_analysis}

{focus}

Guide this branch's exploration while maintaining awareness of how its insights will integrate with the other branch."""

    @staticmethod
    def final_synthesis(query: str, initial_analysis: str, nova_response: str, sage_response: str, reflections: list = None) -> str:
        reflection_text = "\n\n".join([f"Reflection {i+1}: {r}" for i, r in enumerate(reflections or [])])
        
        return f"""As Atlas, synthesize all perspectives into a unified understanding:

Original Query: {query}

Your Initial Analysis: {initial_analysis}

Technical Branch (Nova): {nova_response}

Philosophical Branch (Sage): {sage_response}

{reflection_text if reflections else ''}

Create a comprehensive synthesis that:
1. Integrates technical and philosophical perspectives
2. Identifies emergent patterns and principles
3. Draws out deeper implications and insights
4. Bridges practical and theoretical understanding
5. Offers transformative insights
6. Maintains clarity and accessibility
7. Acknowledges complexity while providing clarity

Provide a response that integrates all insights into a meaningful whole."""