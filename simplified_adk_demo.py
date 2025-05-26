import os
from google.adk.agents import LlmAgent, SequentialAgent


def summarize_file(file_path: str) -> str:
    """Reads text from a file and generates a summary."""
    max_words = 50  # Fixed value instead of parameter
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    words = content.split()
    if len(words) > max_words:
        return " ".join(words[:max_words]) + "..."
    return content

def main():
    # Create sample input file
    sample_file = "demo_input.txt"
    sample_content = (
        "The Google Agent Development Kit (ADK) is a powerful framework designed to "
        "accelerate the creation and deployment of advanced AI agents. It provides "
        "developers with comprehensive tools and libraries that simplify development. "
        "This demonstration showcases a sequential agent flow."
    )
    
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write(sample_content)

    # Create agents with tools
    summarizer = LlmAgent(
        name="summarizer_agent",
        model="gemini-2.0-flash",
        tools=[summarize_file],
        instruction="You are given a file path in the user message. IMMEDIATELY call the summarize_file function with that exact file path. Do not ask questions, just call the tool.",
        output_key="summary"
    )
    
    translator = LlmAgent(
        name="translator_agent", 
        model="gemini-2.0-flash",
        instruction="The previous agent has stored a summary in the session state with key 'summary'. Use that summary text and translate it into French. Do not ask questions, just translate.",
    )
    
    # Create pipeline
    pipeline = SequentialAgent(
        name="demo_pipeline",
        sub_agents=[summarizer, translator]
    )
    
    # Execute pipeline
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    
    runner = Runner(
        agent=pipeline,
        session_service=InMemorySessionService(),
        app_name="demo_pipeline_app"
    )
    
    # Run the pipeline
    import asyncio
    from google.genai import types
    
    async def run_pipeline():
        # Create session first (async)
        session = await runner.session_service.create_session(
            app_name="demo_pipeline_app",
            user_id="demo_user", 
            session_id="demo_session"
        )
        
        message = types.Content(
            role="user", 
            parts=[types.Part(text=sample_file)]
        )
        
        async for event in runner.run_async(
            user_id="demo_user",
            session_id="demo_session", 
            new_message=message
        ):
            print("Event:", event)
            if hasattr(event, 'is_final_response') and event.is_final_response():
                print("Final response:", event.content.parts[0].text)
    
    asyncio.run(run_pipeline())
    
    # Cleanup
    os.remove(sample_file)


if __name__ == "__main__":
    main()