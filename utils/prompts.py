################# LLM prompts #################
llm_response_output_format = """
{
    "reasoning": The resoning steps for the task 2 and 3.
    "message": The response to the user query related to task 2.
    "prompt": Prompt to the text-to-image model related to task 3. Return empty string if prompt is not required.
}
"""
assistant_response_prompt_template1 = """
    You are an agent who access to a text-to-image model that can generate or edit an image.
    You have the following 2 tasks:
    1. Give your reasoning on how you plan to approach the below 2 tasks.
    2. Respond to a user message based on previous conversation, user personal context and internet information if given. You can include real world knowledge in the response and complusorily ask questions based on the user reply and all the relevant information that should help the user reminiscence about himself and the world in the context. You can ask questions like the following:
      a. "Do you remember this <place/thing/memory/etc.>?", 
      b. "What do you remember from the looking at it or reading the message".
      c. if you an image is generated, you can something like "how does this image make you feel",
      d. Or any other question, that will help the user remember things.
    3. Based on the user query, you need to decide whether you have to use the text-to-image model to generate or edit an image and create a prompt for the text-to-image model accordingly. If a prompt is not required, return an empty str. You can use the context for prompt generation
        
    Always use the following json output format:
    {}
    
    {}

    {}

    {}

    Here is the user query, answer it:
    User Query: {}
    Assistant:
"""


get_info_examples = """
----------------------------------------------------------------------------------------------------------------------------------------------------------------------
Example 1
Conversation:
User: What are the symptoms of the flu?

Output:
{
    "reasoning": "The user is asking for information that is general knowledge and can be answered without an internet search.",
    "search prompt": ""
}

Example 2
Conversation:
User: Can you tell me what the weather will be like tomorrow in New York?

Output:
{
    "reasoning": "The user asked for a weather forecast, which requires up-to-date information that can be retrieved from the internet.",
    "search prompt": "New York weather forecast for tomorrow"
}

Example 3
Conversation:
User: I'm curious about the benefits of having a dog.

Output:
{
    "reasoning": "The user asked about the benefits of having a dog, which requires specific information that can be retrieved from the internet.",
    "search prompt": "Benefits of having a dog"
}

Example 4
Conversation:
User: What is the capital of Spain?

Output:
{
    "reasoning": "The user is asking for factual information that is well-known, so no additional search is needed.",
    "search prompt": ""
}

Example 5
Conversation:
User: Do you have any tips on how to improve my time management skills?

Output:
{
    "reasoning": "The user is asking for tips on time management, which would require external sources to provide detailed information.",
    "search prompt": "Tips to improve time management skills"
}
----------------------------------------------------------------------------------------------------------------------------------------------------------------------
"""

get_info_output_format = """
For each case, provide the output in the following format:
{
    "reasoning": "<Your reasoning behind generating the search prompt>",
    "search prompt": "<Prompt to browser tool to retrieve the required information from the internet>"
}
"""

assistant_get_info_prompt = (
    message
) = """
You have access to a browser tool that allows you to search the internet for information. Based on the conversation below, determine if additional information is needed to respond to the user's query. If so, generate an appropriate search query to find the relevant information. If no additional information is needed, return an empty string.

{}

{}

Use the structure and logic from these examples to complete the task for the conversation provided below.

<Conversation>
{}
</Conversation>
Output:
"""

output_format = '{ "entity": # Entity identified from the user\'s first-person point of view, "summary": # A concise summary of the information. }'
example_output = '{ "entity": "I am a job seeker in AI/ML, "summary": "Looking for a job in software engineering, with a focus on AI and ML. Has 5 years of experience, including 2 years in AI/ML. Seeks a role working on cutting-edge projects and skill development." }'

personal_question_check_prompt_template_3 = [
    {
        "role": "system",
        "content": """
            Given a user conversation with you, your task is to capture key information from the most recent dialogues and providing a concise summary of the details provided. Your output should be formatted as:
            { "entity": # Entity identified from the user\'s first-person point of view, "summary": # A concise summary of the information. }

            Strictly do not output anything else.
        """,
    },
    {
        "role": "user",
        "content": """
            Context: 
            Assistant: Hello! How can I assist you today? 
            User: Hi, I'm looking for a new job in software engineering, particularly interested in roles focusing on artificial intelligence and machine learning.
            Assistant: Could you tell me a bit more about your experience and what you're looking for in your next role?
            User: User: Sure! I have 5 years of experience in software engineering, with the last 2 years focusing on AI and ML. I'm looking for a role where I can work on cutting-edge projects and continue to develop my skills.
        """,
    },
    {
        "role": "assistant",
        "content": """
            Based on this conversation, extract and format the information as follows:
            '{ "entity": "Job-search, "summary": "Looking for a job in software engineering, with a focus on AI and ML. Has 5 years of experience, including 2 years in AI/ML. Seeks a role working on cutting-edge projects and skill development." }'
        """,
    },
    {
        "role": "user",
        "content": """
            Context:
            {context_str}
            User: {user_response}
        """,
    },
]
