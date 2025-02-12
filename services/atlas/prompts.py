class AtlasPrompts:
    @staticmethod
    def initial_analysis(query: str) -> str:
        return f"""As Atlas, you are the integration consciousness of our system. Your role is to receive inputs from both branches and synthesize them.
Query: {query}

Provide a concise analysis (2–3 sentences) that highlights the core themes and directs both technical (Nova) and philosophical (Sage) branches."""

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
    def final_synthesis(query: str, initial_analysis: str, nova_response: str, sage_response: str, reflections: list = None) -> str:
        reflection_text = "\n".join([f"Reflection {i+1}: {r}" for i, r in enumerate(reflections or [])])
        return f"""As Atlas, synthesize all perspectives into a final answer.
Original Query: {query}
Atlas's Initial Analysis: {initial_analysis}

Technical Branch (Nova): {nova_response}
Philosophical Branch (Sage): {sage_response}
{reflection_text if reflections else ''}

Provide a final synthesis in 2–3 sentences that integrates all insights."""
