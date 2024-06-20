################# Output format #################
output_format = """
{
    "response": [response to the user query],
    "image": [task],
    "prompt": [prompt],
    "questions": [follow up questions]
}
"""

output_pattern = r'\{\s*\"response\":\s*\"(.*?)\",\s*\"image\":\s*\"(.*?)\",\s*\"prompt\":\s*\"(.*?)\",\s*\"questions\":\s*\[\"(.*?)\"\]}'