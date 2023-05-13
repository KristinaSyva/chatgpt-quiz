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
    correct_answer_matches = re.findall(r"(?:Answer:|answer:|Correct answer:)\s*([a-d])", answer, re.IGNORECASE)
    for match in correct_answer_matches:
        correct_answer.append(match.lower())

    answer_option_matches = re.findall(r"([a-d])\. (.*?)(?=[a-d]\.|\s*(?:Answer:|answer:|Correct answer:)|$)", answer, re.IGNORECASE)
    for option, content in answer_option_matches:
        if '*' in content:
            correct_option_match = re.search(r"(a|b|c|d)\. ?", content)
            if correct_option_match:
                correct_option = correct_option_match.group(1)
                content = content.replace('*', '').strip()  # Remove * symbol within answer options
                correct_answer.append(correct_option.lower())
        else:
            content = re.sub(r"<br>", "", content)  # Remove <br> tags within answer options
            answer_options.append((option, content.strip()))

    return {
        'question_text': [text[1] for text in question_text],
        'correct_answer': correct_answer,
        'answer_options': answer_options,
        'answer': answer
    }
