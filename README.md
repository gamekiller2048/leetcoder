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
client.login("[USERNAME]", "[PASSWORD]")

def get_daily_problem_data():
    # retrive the daily problem
    problem_data = client.get_problem_details('reverse-string')
    question_data = problem_data['question']

    print(f"found daily problem: {question_data['questionTitle']}\nInstructions:\n{question_data['content']}")
    
    # check restrictions of problem
    if question_data['isPaidOnly']:
        raise Exception('problem is paid only')
    if not question_data['enableSubmit']:
        raise Exception('submission is disabled on this problem')
    
    return question_data

def try_solutions(question_data: dict):
    # retrieve first 5 solution articles for the question
    solution_articles = client.get_solution_articles(
        question_slug=question_data['titleSlug'],
        order_by='HOT',
        tag_slugs=['python'],
        skip=0, first=5
    )

    # iterate the articles retrieved
    for i in solution_articles['edges']:
        article = i['node']

        # open the article and retrieve 2 possible solutions to the problem
        # note: solutions are just code tags and may be incorrect / incomplete
        possible_solutions = client.open_solution_article(
            question_slug=question_data['titleSlug'],
            solution_slug=article['slug'],
            topic_id=article['topicId'],
            solution_lang_filter=['python3'],
            max_solutions=2
        )

        # continue if no solutions found in article
        if not possible_solutions:
            continue
        
        # iterate the possible solutions
        for solution in possible_solutions:
            # use the solution written in the first language 
            lang, source = list(solution.items())[0]
            print(f'found solution written in {lang}:\n{source}')

            # submit + poll until finished
            submission_id = client.submit(lang, source, question_id=question_data['questionId'])
            details = poll_submission(submission_id)

            if details['status_msg'] == 'Accepted':
                return
            
def poll_submission(submission_id: int) -> dict:
    details = None
    while True:
        details = client.get_submission_details(submission_id)
        print(details)
        
        if details['state'] == 'SUCCESS':
            break
        
        time.sleep(0.5)

    return details

question_data = get_daily_problem_data()
try_solutions(question_data)
client.quit()
```
### (Note: using this is against the TOS)