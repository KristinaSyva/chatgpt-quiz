import openai
import re
from app.config import DevelopmentConfig

openai.api_key = DevelopmentConfig.OPENAI_KEY

def generateChatResponse(prompt):
    messages = []
    messages.append({"role": "system", "content": "You are a quiz generator. The user gives you a general idea of what kind of quiz they want. You will generate 10 quiz questions unless instructed otherwise after the description and a comma (for example: 'cats are cool, 15'). Each question is followed by correct answer and 3 wrong answers. These 4 options are in random order. Here is an example: 1. What is capital of Estonia? a. Helsinki b. Rome c. Tallinn d. Riga Correct answer: c"})
    
    question = {}
    question['role'] = 'user'
    question['content'] = prompt
    messages.append(question)
    
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    
    try:
        # Remove anything before the first question
        content = re.sub(r'^.*?(?=\n\d+\.|\n$)', '', response['choices'][0]['message']['content'], flags=re.DOTALL)
        # Remove anything after the correct answer
        content = re.sub(r' \w\.\s*\(.*?\)', '', content)
        # Remove any lines that don't start with a number or a b/c/d/C
        content = '\n'.join([line for line in content.split('\n') if re.match(r'^\d|[a-dC]\.', line)])
        # Replace newlines with line breaks
        answer = content.replace('\n', '<br>')
    except:
        answer = "Oops you beat the AI."
    return answer
