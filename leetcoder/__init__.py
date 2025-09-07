from typing import Literal, Union
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from seleniumbase import Driver
import time
import logging
import json
import os

logger = logging.getLogger(__name__)

BASE_URL = 'https://leetcode.com'

OrderBy = Literal['MOST_VOTES', "MOST_RECENT", "HOT"]
LangSlug = Literal['cpp', 'java', 'python3', 'python', 'c', 'csharp', 'javascript', 'typescript', 'php', 'kotlin', 'swift', 'dart', 'go', 'ruby', 'scala', 'rust']
ProblemTypeSlug = Literal[
    'backtracking', 'recursion', 'matrix', 'array', 'hash-table', 'depth-first-search', 
    'bit-manipulation', 'bitmask', 'ordered-set', 'stack', 'dynamic-programming', 
    'math', 'string', 'iterator', 'greedy', 'memoization', 'heap-(priority-queue)', 
    'sorting', 'interactive', 'breadth-first-search', 'tree', 'queue', 'combinatorics', 
    'linked-list', 'hash-function', 'graph', 'enumeration', 'suffix-array', 'brainteaser', 
    'number-theory', 'game-theory', 'simulation']
Tag = Union[LangSlug | ProblemTypeSlug]

def login_required(func):
    def wrapper(self, *args, **kwargs):
        if not self.logged_in:
            raise Exception('client must be logged in to call method')
        return func(self, *args, **kwargs)
    return wrapper


class Client:
    def __init__(self, headless=False, user_data_dir=os.getcwd() + '/UserData'):
        self.driver = Driver(uc=True, headless=headless, user_data_dir=user_data_dir)
        self.logged_in = False

        logger.info(f'client launching {BASE_URL}')
        self.driver.uc_open(BASE_URL)

        if self.driver.get_cookie('csrftoken'):
            self.logged_in = True
            logger.info('logged in as: ' + self.driver.execute_script('return window.LeetCodeData.userStatus.username'))

    def quit(self):
        self.driver.quit()
        
    # this throws NoSuchElementException if not found
    def wait_for_element(self, t: tuple[str, str], timeout_sec=10):
        return WebDriverWait(self.driver, timeout_sec).until(
            EC.presence_of_element_located(t)
        )

    def login(self, username: str, password: str):
        self.driver.uc_open(f'{BASE_URL}/accounts/login/')

        logger.info('waiting on username')
        username_input = self.wait_for_element((By.ID, 'id_login'))

        logger.info('waiting on password')
        password_input = self.wait_for_element((By.ID, 'id_password'))

        logger.info('entering credentials')
        username_input.send_keys(username)
        password_input.send_keys(password)

        logger.info('waiting on captcha (hot fix: wait 3s)')
        # self.wait_for_element((By.ID, 'success-text'))
        time.sleep(3)
        
        logger.info('signing in')
        signin_btn = self.wait_for_element((By.ID, 'signin_btn'))
        signin_btn.click()
        
        logger.info('waiting on homepage')
        self.wait_for_element((By.ID, 'navbar_user_avatar'))

        self.logged_in = True

    def fetch_post(self, url: str, body: Union[str | dict]):
        if type(body) == dict: 
            body = json.dumps(body)
            body = body.replace('"', '\\"')

        csrf = '"x-csrftoken": "' + self.driver.get_cookie('csrftoken')['value'] + '"' if self.logged_in else ''
        script = f"""
        var url = arguments[0];
        var callback = arguments[arguments.length - 1];

        fetch("{url}", {{
        "headers": {{
            "content-type": "application/json",
            {csrf}
        }},
        "referrer": "{self.driver.current_url}",
        "body": "{body}",
        "method": "POST",
        "mode": "cors",
        "credentials": "include"
        }}).then(response => {{
            if(response.ok)
                return response.json();
            return Promise.reject(response);
        }}).then((json) => {{
            callback(json);
        }}).catch((response) => {{
            callback({{"error": response.text}});
        }});
        """

        logger.debug(script)
        data = self.driver.execute_async_script(script)
        logger.debug(f'POST at {url} recieved:\n{data}')
        return data
    
    def fetch_get(self, url: str):
        csrf = '"x-csrftoken": "' + self.driver.get_cookie('csrftoken')['value'] + '"' if self.logged_in else ''
        script = f"""
        var url = arguments[0];
        var callback = arguments[arguments.length - 1];

        fetch("{url}", {{
        "headers": {{
            "content-type": "application/json",
            {csrf}
        }},
        "referrer": "{self.driver.current_url}",
        "method": "GET",
        "mode": "cors",
        "credentials": "include"
        }}).then(response => {{
            if(response.ok)
                return response.json();
            return Promise.reject(response);
        }}).then((json) => {{
            callback(json);
        }}).catch((response) => {{
            callback({{"error": response.text}});
        }});
        """

        logger.debug(script)
        data = self.driver.execute_async_script(script)
        logger.debug(f'GET at {url} recieved:\n{data}')
        return data

    def fetch_graphql(self, query: str, variables: dict, operation_name: str):
        return self.fetch_post(f'{BASE_URL}/graphql', {
            'query': query.replace('\n', '\\n'),
            'variables': variables,
            'operation_name': operation_name
        })

    def get_solution_articles(self, question_slug: str, order_by: OrderBy, tag_slugs: list[Tag], skip: int, first: int, user_input: str = ""):
        return self.fetch_graphql(
            """
            query ugcArticleSolutionArticles(
                $questionSlug: String!,
                $orderBy: ArticleOrderByEnum,
                $userInput: String,
                $tagSlugs: [String!],
                $skip: Int,
                $before: String,
                $after: String,
                $first: Int,
                $last: Int,
                $isMine: Boolean
            ) {
                ugcArticleSolutionArticles(
                    questionSlug: $questionSlug
                    orderBy: $orderBy
                    userInput: $userInput
                    tagSlugs: $tagSlugs
                    skip: $skip
                    first: $first
                    before: $before
                    after: $after
                    last: $last
                    isMine: $isMine
                ) {
                    totalNum
                    edges {
                        node { 
                            slug
                            canSee
                            topicId 
                        }
                    }
                }
            }
            """,
            {
                'questionSlug': question_slug,
                'skip': skip,
                'first': first,
                'orderBy': order_by,
                'userInput': user_input,
                'tagSlugs': tag_slugs
            },
            'ugcArticleSolutionArticles'
        )['data']['ugcArticleSolutionArticles']

    def get_problem_details(self, title_slug: str):
        return self.fetch_graphql(
            """
            query questionDetail($titleSlug: String!) {
                submittableLanguageList { name }
                question(titleSlug: $titleSlug) {
                    questionId
                    questionTitle
                    content
                    isPaidOnly
                    enableRunCode
                    enableSubmit
                    codeSnippets { code langSlug }
                    titleSlug
                }
            }
            """,
            {'titleSlug': title_slug},
            'questionDetail'
            )['data']
    

    def submit(self, lang: LangSlug, source_code: str, question_id: int) -> int:
        source_code = source_code.replace('\n', r'\\n').replace('"', r'\\\"')
        return self.fetch_post(f'{BASE_URL}/problems/sudoku-solver/submit/', f"""
        {{
            \\"lang\\": \\"{lang}\\",
            \\"question_id\\": \\"{question_id}\\",
            \\"typed_code\\": \\"{source_code}\\"
        }}""".replace('\n', '\\n'))['submission_id']

    @login_required
    def get_submission_details(self, submission_id: int):
        return self.fetch_get(f'{BASE_URL}/submissions/detail/{submission_id}/check/')
    
    def get_daily_problem(self) -> dict:
        logger.info('retrieving daily problem')

        title_slug = self.fetch_graphql("""
            query questionOfToday {
                activeDailyCodingChallengeQuestion {
                    question { 
                        titleSlug
                    }
                }
            }
            """,
            {},
            'questionOfToday'
        )['data']['activeDailyCodingChallengeQuestion']['question']['titleSlug']
        
        logger.info(f'found daily problem: {title_slug}\nretrieving more details')
        return self.get_problem_details(title_slug)
        
    def open_solution_article(self, question_slug, solution_slug: str, topic_id: int, solution_lang_filter: list[LangSlug] = [], max_solutions: int = -1):
        logging.warning('this function is error prone as it relies on style tags')

        url = f'{BASE_URL}/problems/{question_slug}/solutions/{topic_id}/{solution_slug}'
        logger.info(f'opening solution article page: ' + url)
        self.driver.get(url)

        logger.info('waiting on solution (hot fix: wait 3s)')
        time.sleep(3)

        logging.debug('finding possible solutions')
        solution_elements = self.driver.find_elements(By.XPATH, '//div[@class="border-gray-3 dark:border-dark-gray-3 mb-6 overflow-hidden rounded-lg border text-sm"]')
        logging.debug(f'found {len(solution_elements)} possible solutions')

        possible_solutions = []

        for el in solution_elements:
            if max_solutions != -1 and len(possible_solutions) >= max_solutions:
                break
            
            logging.debug(f'reading possible solution #{len(possible_solutions)}')

            langs_contianer = el.find_element(By.XPATH, "./div")
            langs = langs_contianer.find_elements(By.XPATH, "./div")
            solution = {}

            for lang in langs:
                l = lang.get_attribute('innerHTML').lower().replace('c++', 'cpp').replace('c#', 'csharp')
                if solution_lang_filter and l not in solution_lang_filter:
                    logging.debug(f'skipping {l}')
                    continue

                logging.debug(f'reading {l}')
                             
                lang.click()
                code_el = el.find_element(By.TAG_NAME, 'code')
                source_code = ""

                lines = code_el.find_elements(By.XPATH, './span')
                for line in lines:
                    keywords = line.find_elements(By.XPATH, './span')

                    for keyword in keywords:
                        source_code += keyword.get_attribute('innerText')

                solution[l] = source_code
            
            if solution:
                possible_solutions.append(solution)
            else:
                logging.debug(f'cannot find requested languages: throwing solution #{len(possible_solutions)}')

        return possible_solutions