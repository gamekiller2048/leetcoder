# Leetcoder
### A minimal leetcode API wrapper I made for a bot using selenium

### Example of an automated bot that solves the daily leetcode by copying solutions:
```python
import leetcoder
import time
import logging

# setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# create a client
client = leetcoder.Client()
client.login("[USER]", "[PASS]")

# fetch daily
question_id, question_slug = client.open_daily_question()

# get the solutions articles
solution_articles = client.get_solution_articles(question_slug, 'HOT', ['python3'], skip=0, first=1)

# retireve info for the first article
article = solution_articles['edges'][0]['node']
solution_slug = article['slug']
topic_id = article['topicId']

# open the first article and get the first possible solution
possible_solutions = client.open_solution_article(question_slug, solution_slug, topic_id, solution_lang_filter=['python3'], max_solutions=1)
lang, source = list(possible_solutions[0].items())[0]

print(f'found solution written in {lang}:\n{source}')

# submit
submission_id = client.submit('python3', possible_solutions[0], question_id)

# poll the state of submission
details = None
while True:
    details = client.get_submission_details(submission_id)
    if details['state'] == 'SUCCESS':
        break
    
    time.sleep(1)

print(details)
client.quit()
```
### (Note: using this is against the TOS)