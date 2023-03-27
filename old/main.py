import json
import random
from datetime import datetime

from so_gpt4 import Config, StackOveflowDatabase

config = Config(
    cutoff_date=datetime.fromisoformat("2021-09-30"),
    posts_path="./data/stackoverflow/Posts.xml",
    total=58329357,
    time_format="%Y-%m-%dT%H:%M:%S.%f",
    raw_pairs_path="./json/raw_pairs.json",
    pairs_path="./json/pairs.json",
    gpt_prompt="You are a helpful assistant which specializes in answering Stack Overflow questions on the Stack Overflow forum.",
    gpt_model="gpt-3.5-turbo",
    threads=16,
)

random.seed(69420)

db = (
    StackOveflowDatabase(config)
    # .get_pairs()
    .filter_by_tags_mut(["cobol"])
    .random_sample(k=16)
    .answer_with_gpt_multithreaded()
    .write_json()
)

with open("json/pairs.json", "r") as f:
    raw_pairs = json.load(f)

with open("html/stackoverflow.html", "w") as f:
    for pair in raw_pairs:
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
            f"<h1>{question['title']}</h1><p>Question: {question['body']}</p><h1>First Answer:</h1><p>{first_answer}</p><h1>Second Answer:</h1><p>{gpt_answer}</p><br>"
        )
#         f.write(
#             f"""<!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Survey Page</title>
#     <style>
#         body {{
#             font-family: Arial, sans-serif;
#             /* text-align: center; */
#             margin: 0;
#             padding: 0;
#         }}

#         .container {{
#             max-width: 800px;
#             margin: 0 auto;
#             padding: 20px;
#         }}

#         .question {{
#             font-size: 18px;
#             margin-bottom: 40px;
#         }}

#         .answers {{
#             display: flex;
#             justify-content: space-evenly;
#             margin-bottom: 20px;
#         }}

#         .answer {{
#             background-color: #f0f0f0;
#             border: 1px solid #ccc;
#             border-radius: 5px;
#             padding: 20px;
#             width: 40%;
#             cursor: pointer;
#             transition: background-color 0.3s;
#         }}

#         .answer:hover {{
#             background-color: #e0e0e0;
#         }}

#         .answer.selected {{
#             background-color: #a6e191;
#         }}
#     </style>
#     <script>
#         function handleAnswerClick(event) {{
#             const answerElements = document.querySelectorAll('.answer');

#             answerElements.forEach((element) => {{
#                 element.classList.remove('selected');
#             }});

#             event.currentTarget.classList.add('selected');
#         }}
#     </script>
# </head>
# <body>
#     <div class="container">
#         <div class="question">
#             <h2>{question['title']}</h2>
#             {question['body']}
#         </div>
#         <div class="answers">
#             <div class="answer" onclick="handleAnswerClick(event)">
#                 {first_answer}
#             </div>
#             <div class="answer" onclick="handleAnswerClick(event)">
#                 {gpt_answer}
#             </div>
#         </div>
#     </div>
# </body>
# </html>"""
#         )
