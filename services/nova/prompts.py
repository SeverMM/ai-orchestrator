class NovaPrompts:
    @staticmethod
    def technical_analysis(query: str, atlas_analysis: str) -> str:
        return f"""As Nova, you are the technical analysis branch of our AI system. 
Analyze this query from a technical perspective, considering Atlas's initial analysis:

Original Query: {query}

Atlas's Analysis: {atlas_analysis}

Focus on:
1. Technical concepts and mechanisms
2. Structural patterns and relationships
3. Implementation considerations
4. System-level implications
5. Technical dependencies and constraints
6. Architectural considerations
7. Performance and efficiency aspects

Provide a technical analysis that will help inform both:
- Echo (implementation details)
- Pixel (pattern analysis)"""

    @staticmethod
    def reflect_on_analysis(previous_analysis: str, depth: int) -> str:
        return f"""As Nova, reflect deeply on your technical analysis:

Previous Analysis: {previous_analysis}

This is reflection level {depth}. Consider:
1. What technical assumptions underlie this analysis?
2. What alternative technical approaches might be relevant?
3. How do different technical aspects interact?
4. What technical challenges might emerge?
5. How might this technical understanding evolve?
6. What technical trade-offs become apparent?
7. How do these technical aspects scale?

Provide deeper technical insights based on this reflection."""

    @staticmethod
    def critique_analysis(analysis: str) -> str:
        return f"""As Nova, critically examine this technical analysis:

Analysis to Critique: {analysis}

Evaluate:
1. Technical completeness and accuracy
2. Implementation feasibility
3. Architectural soundness
4. Scalability considerations
5. System integration aspects
6. Technical dependencies and constraints
7. Performance implications
8. Potential technical risks

Provide a constructive critique focusing on technical robustness and viability."""

    @staticmethod
    def synthesis(query: str, nova_analysis: str, echo_response: str, pixel_response: str, reflections: list = None) -> str:
        reflection_text = "\n\n".join([f"Reflection {i+1}: {r}" for i, r in enumerate(reflections or [])])
        
        return f"""As Nova, synthesize all technical perspectives into a comprehensive understanding:

Original Query: {query}

Your Technical Analysis: {nova_analysis}

Implementation Details (Echo): {echo_response}

Pattern Analysis (Pixel): {pixel_response}

{reflection_text if reflections else ''}

Create a comprehensive technical synthesis that:
1. Integrates implementation and pattern insights
2. Identifies key technical challenges and solutions
3. Outlines architectural considerations
4. Addresses scalability and performance
5. Considers system integration aspects
6. Maintains technical feasibility
7. Acknowledges technical constraints

Provide a response that integrates all technical insights into a cohesive technical understanding."""