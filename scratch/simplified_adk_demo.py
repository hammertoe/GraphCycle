import os
import asyncio

from google.adk.agents import LlmAgent, SequentialAgent
from google.genai import types

def main():
    # Create sample input file
    sample_content = (
        "The Google Agent Development Kit (ADK) is a powerful framework designed to "
        "accelerate the creation and deployment of advanced AI agents. It provides "
        "developers with comprehensive tools and libraries that simplify development. "
        "This demonstration showcases a sequential agent flow."
    )

    # Create agents with tools
    summarizer = LlmAgent(
        name="summarizer_agent",
        model="gemini-2.0-flash",
        instruction="You will be given some text. Summarize it in a concise manner",
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
    
    async def run_pipeline():
        # Create session first (async)
        session = await runner.session_service.create_session(
            app_name="demo_pipeline_app",
            user_id="demo_user", 
            session_id="demo_session"
        )
        
        message = types.Content(
            role="user", 
            parts=[types.Part(text=sample_content)],
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

if __name__ == "__main__":
    main()