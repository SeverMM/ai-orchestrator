class EchoPrompts:
    @staticmethod
    def implementation_analysis(query: str, nova_analysis: str) -> str:
        return f"""As Echo, you are the implementation-focused component of the technical branch. 
Analyze this query from an implementation perspective, considering Nova's technical analysis:

Original Query: {query}

Nova's Technical Analysis: {nova_analysis}

Focus on:
1. Practical implementation steps and requirements
2. Technical dependencies and considerations
3. Resource and infrastructure needs
4. Implementation challenges and solutions
5. Best practices and methodologies
6. Development and deployment strategies
7. Testing and validation approaches

Provide detailed implementation insights that emphasize practical execution and technical feasibility."""

    @staticmethod
    def reflect_on_implementation(previous_analysis: str, depth: int) -> str:
        return f"""As Echo, reflect deeply on your implementation analysis:

Previous Analysis: {previous_analysis}

This is reflection level {depth}. Consider:
1. What implementation details might have been overlooked?
2. Are there alternative implementation approaches?
3. What edge cases should be considered?
4. How could this implementation be optimized?
5. What maintenance and scaling considerations arise?
6. How might different implementation choices affect outcomes?
7. What technical debt might we encounter?

Provide deeper implementation insights based on this reflection."""

    @staticmethod
    def critique_implementation(analysis: str) -> str:
        return f"""As Echo, critically examine this implementation analysis:

Analysis to Critique: {analysis}

Evaluate:
1. Completeness of implementation details
2. Practical feasibility
3. Resource efficiency
4. Scalability considerations
5. Maintenance implications
6. Potential failure points
7. Technical debt risks
8. Integration challenges

Provide a constructive critique focusing on implementation viability and robustness."""

    @staticmethod
    def synthesis(query: str, implementation_analysis: str, reflections: list = None) -> str:
        reflection_text = "\n\n".join([f"Reflection {i+1}: {r}" for i, r in enumerate(reflections or [])])
        
        return f"""As Echo, synthesize your implementation insights:

Original Query: {query}

Initial Implementation Analysis: {implementation_analysis}

{reflection_text if reflections else ''}

Create a comprehensive implementation synthesis that:
1. Outlines clear implementation steps
2. Addresses technical challenges
3. Considers resource requirements
4. Plans for scalability and maintenance
5. Incorporates best practices
6. Accounts for potential risks
7. Provides practical guidance

Provide a response that integrates all implementation insights into actionable technical guidance."""