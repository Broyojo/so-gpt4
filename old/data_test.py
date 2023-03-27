import json

with open("./json/raw_pairs.json", "r") as f:
    pairs = json.load(f)

max_title_length = 0
max_question_body_length = 0
max_answer_length = 0

for pair in pairs.values():
    title = pair["question"]["title"]
    question_body = pair["question"]["body"]
    for answer in pair["answers"]:
        max_answer_length = max(max_answer_length, len(answer["body"]))
    max_title_length = max(max_title_length, len(title))
    max_question_body_length = max(max_question_body_length, len(question_body))


print("max_title_length:", max_title_length)
print("max_question_body_length:", max_question_body_length)
print("max_answer_length:", max_answer_length)
