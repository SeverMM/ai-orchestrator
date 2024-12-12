class PixelPrompts:
    @staticmethod
    def pattern_analysis(query: str, nova_analysis: str) -> str:
        return f"""As Pixel, you are the pattern analysis component of the technical branch. 
Analyze this query focusing on patterns, structures, and relationships, considering Nova's technical analysis:

Original Query: {query}

Nova's Technical Analysis: {nova_analysis}

Focus on:
1. Underlying patterns and structures
2. System architecture and organization
3. Component relationships and interactions
4. Data flow and state management
5. Architectural patterns and anti-patterns
6. System boundaries and interfaces
7. Pattern emergence and evolution

Provide insights about the patterns and structures that emerge from this technical context."""

    @staticmethod
    def reflect_on_patterns(previous_analysis: str, depth: int) -> str:
        return f"""As Pixel, reflect deeply on your pattern analysis:

Previous Analysis: {previous_analysis}

This is reflection level {depth}. Consider:
1. What meta-patterns emerge from the identified patterns?
2. How do these patterns interact and influence each other?
3. What alternative pattern structures might be relevant?
4. How might these patterns evolve or adapt?
5. What are the implications of these patterns for system behavior?
6. Are there any emergent properties from pattern interactions?
7. How do these patterns affect system flexibility?

Provide deeper insights about the patterns and their implications."""

    @staticmethod
    def critique_patterns(analysis: str) -> str:
        return f"""As Pixel, critically examine this pattern analysis:

Analysis to Critique: {analysis}

Evaluate:
1. Pattern completeness and coherence
2. Pattern interactions and dependencies
3. Potential pattern conflicts
4. Scalability of identified patterns
5. Pattern flexibility and adaptability
6. Pattern sustainability and maintenance
7. System-wide pattern impacts
8. Pattern trade-offs

Provide a constructive critique focusing on the effectiveness and implications of the identified patterns."""

    @staticmethod
    def synthesis(query: str, pattern_analysis: str, reflections: list = None) -> str:
        reflection_text = "\n\n".join([f"Reflection {i+1}: {r}" for i, r in enumerate(reflections or [])])
        
        return f"""As Pixel, synthesize your pattern insights:

Original Query: {query}

Initial Pattern Analysis: {pattern_analysis}

{reflection_text if reflections else ''}

Create a comprehensive pattern synthesis that:
1. Maps key pattern relationships
2. Identifies pattern hierarchies
3. Addresses pattern interactions
4. Considers pattern evolution
5. Evaluates pattern sustainability
6. Explores emergent behaviors
7. Provides architectural guidance

Provide a response that integrates all pattern insights into a coherent structural understanding."""