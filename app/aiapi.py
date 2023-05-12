import openai
import re
from app.config import DevelopmentConfig

openai.api_key = DevelopmentConfig.OPENAI_KEY


def generateChatResponse(prompt):
    messages = []
    messages.append({
        "role": "system",
        "content": "You are a quiz generator. The user gives you one word or a sentence. You will generate 10 quiz questions on the topic unless instructed otherwise. Each question is followed by the correct answer and 3 wrong answers. These 4 options are in random order. Here is an example: 1. What is the capital of Estonia? a. Helsinki b. Rome c. Tallinn d. Riga Correct answer: a DO NOT ADD A DOT (.) or anything else AFTER THIS"
    })

    question = {
        "role": "user",
        "content": prompt
    }
    messages.append(question)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    try:
        answer = response['choices'][0]['message']['content'].replace('\n', '<br>')
    except:
        answer = "Oops, you beat the AI."

    # Extract question and answer from the cleaned answer string
    question_text = re.findall(r"(\d+\.)\s(.*?)<br>", answer)

    correct_answer = []
    answer_options = []
    for match in re.findall(r"([a-d])\. (.*?)(?=[a-d]\.|\s*Correct answer:|$)", answer):
        option, content = match
        if '*' in content:
            correct_option = re.search(r"(a|b|c|d)\. ?", content)
            if correct_option:
                correct_option = correct_option.group(1)
                content = content.replace('*', '').strip()  # Remove * symbol within answer options
                correct_answer.append(correct_option)
        else:
            content = re.sub(r"<br>", "", content)  # Remove <br> tags within answer options
            answer_options.append((option, content.strip()))

    # Extract correct answers from the answer string
    correct_answer_lines = re.findall(r"Answer:\s*([a-d])", answer, re.IGNORECASE)
    correct_answer = [option.lower() for option in correct_answer_lines]

    #print("Extracted Question Text:")
    #print([text[1] for text in question_text])
    #print("Correct Answer:")
    #print(correct_answer)
    #print("Answer Options:")
    #print(answer_options)

    return {
        'question_text': [text[1] for text in question_text],
        'correct_answer': correct_answer,
        'answer_options': answer_options
    }
