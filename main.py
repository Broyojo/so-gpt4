import json
import random
from datetime import datetime

from so_gpt4 import Config, StackOveflowDatabase

config = Config(
    cutoff_date=datetime.fromisoformat("2021-09-30"),
    posts_path="./data/cooking/Posts.xml",
    total=88706,
    time_format="%Y-%m-%dT%H:%M:%S.%f",
    pairs_path="./json/pairs.json",
    gpt_prompt="You are a helpful assistant which specializes in answering cooking questions on the cooking stack exchange forum. You may format your answer using HTML if necessary, such as making it more clear, adding tables, bullet points, links, etc.",
    gpt_model="gpt-3.5-turbo",
)

db = (
    StackOveflowDatabase(config)
    .get_pairs()
    .random_sample(k=10)
    .answer_with_gpt()
    .write_json()
)

with open("json/pairs.json", "r") as f:
    pairs = json.load(f)

with open("html/cooking.html", "w") as f:
    for pair in pairs:
        question = pair["question"]
        first_answer = min(
            pair["answers"], key=lambda a: datetime.fromisoformat(a["creation_date"])
        )["body"]
        gpt_answer = pair["gpt_answer"]

        if random.random() < 0.5:
            temp = first_answer
            first_answer = gpt_answer
            gpt_answer = temp

        f.write(
            f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Survey Page</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            /* text-align: center; */
            margin: 0;
            padding: 0;
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}

        .question {{
            font-size: 24px;
            margin-bottom: 40px;
        }}

        .answers {{
            display: flex;
            justify-content: space-evenly;
            margin-bottom: 20px;
        }}

        .answer {{
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 20px;
            width: 40%;
            cursor: pointer;
            transition: background-color 0.3s;
        }}

        .answer:hover {{
            background-color: #e0e0e0;
        }}

        .answer.selected {{
            background-color: #a6e191;
        }}
    </style>
    <script>
        function handleAnswerClick(event) {{
            const answerElements = document.querySelectorAll('.answer');

            answerElements.forEach((element) => {{
                element.classList.remove('selected');
            }});

            event.currentTarget.classList.add('selected');
        }}
    </script>
</head>
<body>
    <div class="container">
        <div class="question">
            <h2>{question['title']}</h2>
            {question['body']}
        </div>
        <div class="answers">
            <div class="answer" onclick="handleAnswerClick(event)">
                {first_answer}
            </div>
            <div class="answer" onclick="handleAnswerClick(event)">
                {gpt_answer}
            </div>
        </div>
    </div>
</body>
</html>"""
        )
