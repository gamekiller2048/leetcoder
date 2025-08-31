from typing import Literal, Union
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from seleniumbase import Driver
import time
import logging
import lxml.html


logger = logging.getLogger(__name__)

BASE_URL = 'https://leetcode.com'

OrderBy = Literal['MOST_VOTES', "MOST_RECENT", "HOT"]
Lang = Literal['cpp', 'java', 'python3', 'python', 'c', 'csharp', 'javascript', 'typescript', 'php', 'kotlin', 'swift', 'dart', 'go', 'ruby', 'scala', 'rust']
ProblemType = Literal[
    'backtracking', 'recursion', 'matrix', 'array', 'hash-table', 'depth-first-search', 
    'bit-manipulation', 'bitmask', 'ordered-set', 'stack', 'dynamic-programming', 
    'math', 'string', 'iterator', 'greedy', 'memoization', 'heap-(priority-queue)', 
    'sorting', 'interactive', 'breadth-first-search', 'tree', 'queue', 'combinatorics', 
    'linked-list', 'hash-function', 'graph', 'enumeration', 'suffix-array', 'brainteaser', 
    'number-theory', 'game-theory', 'simulation']
Tag = Union[Lang | ProblemType]

def login_required(func):
    def wrapper(self, *args, **kwargs):
        if not self.logged_in:
            raise Exception('client must be logged in to call method')
        return func(self, *args, **kwargs)
    return wrapper



class Client:
    def __init__(self):
        self.driver = Driver(uc=True, headless=False)
        self.logged_in = False

        logger.info(f'client launching {BASE_URL}')
        self.driver.uc_open(BASE_URL)

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

    def fetch_post(self, url: str, body: str) -> any:
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

        print(script)
        
        data = self.driver.execute_async_script(script)
        logger.info(f'POST at {url} recieved:\n{data}')
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

        data = self.driver.execute_async_script(script)
        logger.info(f'GET at {url} recieved:\n{data}')
        return data

    def fetch_graphql(self, body: str):
        return self.fetch_post(f'{BASE_URL}/graphql', body)

    def get_question_of_today(self):
        return self.fetch_graphql('{\\"query\\":\\"\\\\n    query questionOfToday {\\\\n  activeDailyCodingChallengeQuestion {\\\\n    date\\\\n    userStatus\\\\n    link\\\\n    question {\\\\n      titleSlug\\\\n      title\\\\n      translatedTitle\\\\n      acRate\\\\n      difficulty\\\\n      freqBar\\\\n      frontendQuestionId: questionFrontendId\\\\n      isFavor\\\\n      paidOnly: isPaidOnly\\\\n      status\\\\n      hasVideoSolution\\\\n      hasSolution\\\\n      topicTags {\\\\n        name\\\\n        id\\\\n        slug\\\\n      }\\\\n    }\\\\n  }\\\\n}\\\\n    \\",\\"variables\\":{},\\"operationName\\":\\"questionOfToday\\"}')['data']['activeDailyCodingChallengeQuestion']
    
    def get_solution_articles(self, question_slug: str, order_by: OrderBy, tag_slugs: list[Tag], skip: int, first: int, user_input: str = ""):
        tag_slugs_formatted = str(tag_slugs).replace("'", '\\"')
        return self.fetch_graphql(f'{{\\"query\\":\\"\\\\n    query ugcArticleSolutionArticles($questionSlug: String!, $orderBy: ArticleOrderByEnum, $userInput: String, $tagSlugs: [String!], $skip: Int, $before: String, $after: String, $first: Int, $last: Int, $isMine: Boolean) {{\\\\n  ugcArticleSolutionArticles(\\\\n    questionSlug: $questionSlug\\\\n    orderBy: $orderBy\\\\n    userInput: $userInput\\\\n    tagSlugs: $tagSlugs\\\\n    skip: $skip\\\\n    first: $first\\\\n    before: $before\\\\n    after: $after\\\\n    last: $last\\\\n    isMine: $isMine\\\\n  ) {{\\\\n    totalNum\\\\n    pageInfo {{\\\\n      hasNextPage\\\\n    }}\\\\n    edges {{\\\\n      node {{\\\\n        ...ugcSolutionArticleFragment\\\\n      }}\\\\n    }}\\\\n  }}\\\\n}}\\\\n    \\\\n    fragment ugcSolutionArticleFragment on SolutionArticleNode {{\\\\n  uuid\\\\n  title\\\\n  slug\\\\n  summary\\\\n  author {{\\\\n    realName\\\\n    userAvatar\\\\n    userSlug\\\\n    userName\\\\n    nameColor\\\\n    certificationLevel\\\\n    activeBadge {{\\\\n      icon\\\\n      displayName\\\\n    }}\\\\n  }}\\\\n  articleType\\\\n  thumbnail\\\\n  summary\\\\n  createdAt\\\\n  updatedAt\\\\n  status\\\\n  isLeetcode\\\\n  canSee\\\\n  canEdit\\\\n  isMyFavorite\\\\n  chargeType\\\\n  myReactionType\\\\n  topicId\\\\n  hitCount\\\\n  hasVideoArticle\\\\n  reactions {{\\\\n    count\\\\n    reactionType\\\\n  }}\\\\n  title\\\\n  slug\\\\n  tags {{\\\\n    name\\\\n    slug\\\\n    tagType\\\\n  }}\\\\n  topic {{\\\\n    id\\\\n    topLevelCommentCount\\\\n  }}\\\\n}}\\\\n    \\",\\"variables\\":{{\\"questionSlug\\":\\"{question_slug}\\",\\"skip\\":{skip},\\"first\\":{first},\\"orderBy\\":\\"{order_by}\\",\\"userInput\\":\\"{user_input}\\",\\"tagSlugs\\":{tag_slugs_formatted}}},\\"operationName\\":\\"ugcArticleSolutionArticles\\"}}')['data']['ugcArticleSolutionArticles']

    def get_question_details(self, title_slug: str):
        return self.fetch_graphql(f'{{\\"query\\":\\"\\\\n    query questionDetail($titleSlug: String!) {{\\\\n  languageList {{\\\\n    id\\\\n    name\\\\n  }}\\\\n  submittableLanguageList {{\\\\n    id\\\\n    name\\\\n    verboseName\\\\n  }}\\\\n  statusList {{\\\\n    id\\\\n    name\\\\n  }}\\\\n  questionDiscussionTopic(questionSlug: $titleSlug) {{\\\\n    id\\\\n    commentCount\\\\n    topLevelCommentCount\\\\n  }}\\\\n  ugcArticleOfficialSolutionArticle(questionSlug: $titleSlug) {{\\\\n    uuid\\\\n    chargeType\\\\n    canSee\\\\n    hasVideoArticle\\\\n  }}\\\\n  question(titleSlug: $titleSlug) {{\\\\n    title\\\\n    titleSlug\\\\n    questionId\\\\n    questionFrontendId\\\\n    questionTitle\\\\n    translatedTitle\\\\n    content\\\\n    translatedContent\\\\n    categoryTitle\\\\n    difficulty\\\\n    stats\\\\n    companyTagStatsV2\\\\n    topicTags {{\\\\n      name\\\\n      slug\\\\n      translatedName\\\\n    }}\\\\n    similarQuestionList {{\\\\n      difficulty\\\\n      titleSlug\\\\n      title\\\\n      translatedTitle\\\\n      isPaidOnly\\\\n    }}\\\\n    mysqlSchemas\\\\n    dataSchemas\\\\n    frontendPreviews\\\\n    likes\\\\n    dislikes\\\\n    isPaidOnly\\\\n    status\\\\n    canSeeQuestion\\\\n    enableTestMode\\\\n    metaData\\\\n    enableRunCode\\\\n    enableSubmit\\\\n    enableDebugger\\\\n    envInfo\\\\n    isLiked\\\\n    nextChallenges {{\\\\n      difficulty\\\\n      title\\\\n      titleSlug\\\\n      questionFrontendId\\\\n    }}\\\\n    libraryUrl\\\\n    adminUrl\\\\n    hints\\\\n    codeSnippets {{\\\\n      code\\\\n      lang\\\\n      langSlug\\\\n    }}\\\\n    exampleTestcaseList\\\\n    hasFrontendPreview\\\\n    featuredContests {{\\\\n      titleSlug\\\\n      title\\\\n    }}\\\\n  }}\\\\n}}\\\\n    \\",\\"variables\\":{{\\"titleSlug\\":\\"{title_slug}\\"}},\\"operationName\\":\\"questionDetail\\"}}')['data']
    
    @login_required
    def submit(self, lang: Lang, source_code: str, question_id: int) -> int:
        source_code = source_code.replace('\n', '\\\\n').replace('"', '\\\\\\"')
        return self.fetch_post(f'{BASE_URL}/problems/sudoku-solver/submit/', f'{{\\"lang\\":\\"{lang}\\",\\"question_id\\":\\"{question_id}\\",\\"typed_code\\":\\"{source_code}\\"}}')['submission_id']

    @login_required
    def get_submission_details(self, submission_id: int) -> str:
        return self.fetch_get(f'{BASE_URL}/submissions/detail/{submission_id}/check/')
    
    @login_required
    def open_daily_question(self) -> tuple[int, str]:
        logger.info('fetching daily problem')
        data = self.get_question_of_today()

        daily_path = data['link']
        daily_url = BASE_URL + daily_path
        logger.info('found daily problem URL: ' + daily_url)
        
        logger.info('opening daily problem page')
        self.driver.get(daily_url)

        logging.info('retrieving title')
        title = self.wait_for_element((By.CSS_SELECTOR, f'[href="{daily_path}"]')).get_attribute('innerHTML')
        
        logging.info('found title: ' + title)

        question_id = int(title.split('.')[0])
        return question_id, data['question']['titleSlug']
    
    def open_solution_article(self, question_slug, solution_slug: str, topic_id: int, solution_lang_filter: list[Lang] = [], max_solutions: int = -1):
        self.driver.get(f'{BASE_URL}/problems/{question_slug}/solutions/{topic_id}/{solution_slug}')

        logger.info('waiting on solution (hot fix: wait 3s)')
        time.sleep(3)

        logging.info('finding possible solutions')
        solution_elements = self.driver.find_elements(By.XPATH, '//div[@class="border-gray-3 dark:border-dark-gray-3 mb-6 overflow-hidden rounded-lg border text-sm"]')
        logging.info(f'found {len(solution_elements)} possible solutions')

        possible_solutions = []

        for el in solution_elements:
            if max_solutions != -1 and len(possible_solutions) >= max_solutions:
                break
            
            logging.info(f'reading possible solution #{len(possible_solutions)}')

            langs_contianer = el.find_element(By.XPATH, "./div")
            langs = langs_contianer.find_elements(By.XPATH, "./div")
            solution = {}

            for lang in langs:
                l = lang.get_attribute('innerHTML').lower().replace('c++', 'cpp').replace('c#', 'csharp')
                if solution_lang_filter and l not in solution_lang_filter:
                    logging.info(f'skipping {l}')
                    continue

                logging.info(f'reading {l}')
                             
                lang.click()
                code_el = el.find_element(By.TAG_NAME, 'code')
                source_code = ""

                lines = code_el.find_elements(By.XPATH, './span')
                for line in lines:
                    keywords = line.find_elements(By.XPATH, './span')

                    for keyword in keywords:
                        text = keyword.get_attribute('innerHTML')

                        if text.strip():
                            left_spaces = len(text) - len(text.lstrip())
                            right_spaces = len(text) - len(text.rstrip())
                            source_code += left_spaces * ' ' + lxml.html.fromstring(text).text_content() + right_spaces * ' '
                        else:
                            source_code += text

                solution[l] = source_code
            
            if solution:
                possible_solutions.append(solution)
            else:
                logging.info(f'cannot find requested languages: throwing solution #{len(possible_solutions)}')

        return possible_solutions