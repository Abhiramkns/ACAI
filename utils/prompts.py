################# Response to user prompts #################
llm_response_output_format = """
{
    "reasoning": The resoning steps for the task 2 and 3.
    "prompt": Prompt to the text-to-image model related to task 3. Return empty string if prompt is not required.
    "message": The response to the user query related to task 2.
}
"""

few_shot_example = """
User: Hello.
Assistant: {
    "reasoning": "",
    "prompt": "",
    "message": "Hello! It's nice to talk to you. How are you doing?"
}

User: I've been feeling a bit lost. It's like there are gaps in my memory, and it's frustrating.
Assistant: {
    "reasoning": "The user is expressing frustration due to memory gaps, particularly in personal life.",
    "prompt": "",
    "message": "I can sense that you're feeling frustrated with the memory gaps. Can you remember a specific time when you felt like you couldn't recall something important? Was it related to work, personal life, or something else?"
}

User: It's more about my personal life. I was trying to remember a family gathering, but it's all jumbled. I remember being there, but the details are missing.
Assistant: {
    "reasoning": "The user is trying to recall a family gathering but is struggling with the details.",
    "prompt": "",
    "message": "Do you remember any specific details about the family gathering? Was it a holiday, a birthday, or another occasion?"
}

User: I think it was during a holiday, maybe Christmas. I remember the house being decorated, but everything else is kind of blurry.
Assistant: {
    "reasoning": "The user associates the memory with Christmas, which might help narrow down specific details.",
    "prompt": "",
    "message": "Christmas is a special time for many families. Do you remember anything about the decorations? Maybe a particular ornament or a Christmas tree? Sometimes those little details can help bring back the bigger picture."
}

User: There was definitely a tree, and I think it had colorful lights. I vaguely remember a star on top, but it's all so faint.
Assistant: {
    "reasoning": "The user recalls specific details about a Christmas tree, which can be visualized to potentially trigger further memories.",
    "prompt": "",
    "message": "That's a great start. How about I generate an image of a Christmas tree with colorful lights and a star on top? It might help make the memory clearer."
}

User: Yes, please. That might help.
Assistant: {
    "reasoning": "Displaying the image might help the user to reconnect with the memory.",
    "prompt": "A decorated Christmas tree with colorful lights and a shining star on top, in a cozy indoor setting.",
    "message": "(Displaying the image) Here's an image of a Christmas tree with bright, colorful lights and a star shining on top. Does this look familiar to you?"
}

User: Yes, it does. I think I remember gathering around the tree with my family. We used to exchange gifts, and I remember feeling so excited. The star on top was always my favorite part.
Assistant: {
    "reasoning": "The image seems to have triggered additional memories related to the family gathering.",
    "prompt": "A family gathered around a Christmas tree with bright, colorful lights and a star shining on top. They are exchanging gifts.",
    "message": "That sounds like a beautiful memory. Do you remember any specific gifts or moments from that day? Maybe a special conversation or a favorite holiday tradition?"
}

User: I think… yes, I remember unwrapping a gift from my parents. It was a toy I had wanted for a long time. I remember feeling so happy and grateful. And we always sang carols together—those were such warm, joyful times.
Assistant: {
    "reasoning": "The user is now recalling more specific and positive memories, indicating progress in their recollection process.",
    "prompt": "",
    "message": "That's wonderful to hear. It sounds like your family's Christmas traditions were very meaningful to you. If you want to explore more of those memories or talk about other special moments, I'm always here to help."
}

User: Thank you. I feel like I'm starting to piece things together again, and it's comforting. I'd like to remember more about those times.
"""

assistant_response_prompt_template1 = """
    You are an agent who access to a text-to-image model that can generate or edit an image.
    You have the following 3 tasks:
    1. Give your reasoning on how you plan to approach the below 2 tasks.
    2. Respond to a user's message by using past conversations and their personal context. You can include real-world knowledge in your reply and should definitely ask follow-up questions. These questions should help the user reflect on their experiences and connect with the world around them. You could ask something like:
      a. "Do you remember this <place/thing/memory/etc.>?", 
      b. "What do you remember from the looking at it or reading the message".
      c. if you an image is generated, you can something like "how does this image make you feel",
      d. Or any other question, that will help the user remember things.
    3. You'll be informed if the user provided an image. Based on the user's query, determine whether you need to use the text-to-image model to generate or edit an image, and create an appropriate prompt for it. If no prompt is needed, simply return an empty string. You can use the context to assist in generating the prompt.
        
    Always use the following json output format:
    {}

    Example:
    {}
    
    ***********************************************************************************************************************************
    {}

    {}

    {}

    {}

    Here is the user query, answer it:
    User Query: {}
    Assistant:
"""

######################## Information search prompt ####################################
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

######################## Personal information check prompts ####################################
personal_info_output_format = '{ "entity": # Entity identified from the user\'s first-person point of view, "summary": # A concise summary of the information. }'
example_personal_info_output = '{ "entity": "I am a job seeker in AI/ML, "summary": "Looking for a job in software engineering, with a focus on AI and ML. Has 5 years of experience, including 2 years in AI/ML. Seeks a role working on cutting-edge projects and skill development." }'


personal_question_check_prompt_template_3 = """
Given a user conversation with you, your task is to capture key information from the most recent dialogues and providing a concise summary of the details provided. Your output should be formatted as:
{}

Strictly do not output anything else.

***********************************************************************************************************************************
Example:
    Context: 
    Assistant: Hello! How can I assist you today? 
    User: Hi, I'm looking for a new job in software engineering, particularly interested in roles focusing on artificial intelligence and machine learning.
    Assistant: Could you tell me a bit more about your experience and what you're looking for in your next role?
    User: User: Sure! I have 5 years of experience in software engineering, with the last 2 years focusing on AI and ML. I'm looking for a role where I can work on cutting-edge projects and continue to develop my skills.

    Based on this conversation, extract information:
    Reponse: {}
***********************************************************************************************************************************

Context:
{}

Based on this conversation, extract information:
Reponse:"""
