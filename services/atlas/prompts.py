from database.models import ThinkingType, ProcessingStage

class AtlasPrompts:
    @staticmethod
    def initial_analysis(query: str) -> str:
        return f"""As Atlas, you are the integration consciousness of our system. Your role is to receive inputs from both branches and synthesize them.
Query: {query}

Provide a concise analysis (2–3 sentences) that highlights the core themes."""

    @staticmethod
    def reflect_on_analysis(previous_analysis: str, depth: int) -> str:
        return f"""As Atlas, reflect on your previous analysis (Reflection Level {depth}):
Previous Analysis: {previous_analysis}

Provide a brief reflection in 2–3 sentences, identifying any emergent patterns or higher-order insights."""

    @staticmethod
    def critique_analysis(analysis: str) -> str:
        return f"""As Atlas, critique the following analysis:
Analysis: {analysis}

Provide a 2–3 sentence critique focusing on strengths, weaknesses, and suggestions for deeper integration."""

    @staticmethod
    def branch_specific_guidance(original_query: str, initial_analysis: str, branch: str) -> str:
        if branch.lower() == "nova":
            focus = "technical aspects, including systems, patterns, and dependencies"
        else:  # for "sage"
            focus = "philosophical aspects, such as abstract meanings, ethical considerations, and cultural context"
        return f"""As Atlas, guide the {branch} branch.
Original Query: {original_query}
Atlas's Analysis: {initial_analysis}

Focus on {focus}. Provide concise instructions (2–3 sentences) for their analysis."""

    @staticmethod
    def final_synthesis(query: str, atlas_analysis: str, nova_response: str, sage_response: str) -> str:
        """Generate a prompt for final synthesis of all responses."""
        return f"""As Atlas, you are tasked with synthesizing multiple perspectives into a cohesive final response.

Context:
Original Query: {query}

Your Initial Analysis: {atlas_analysis}

Technical Perspective (Nova): {nova_response}

Philosophical Perspective (Sage): {sage_response}

Instructions:
1. Consider your initial analysis, Nova's technical insights, and Sage's philosophical perspective
2. Create a balanced synthesis that integrates all viewpoints
3. Ensure the response directly addresses the original query
4. Keep the synthesis clear, concise, and actionable
5. Present the information in a way that provides immediate value to the user

Please provide your synthesized response:"""
