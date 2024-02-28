import time
import logging
from string import Template
from typing import List

from openai import OpenAI, RateLimitError

from .utils import NoAvailableAPIKey, APIKeyPool


logger = logging.getLogger(__name__)
COMPRESS_USER_PROMPT = '''Compress the following text: $user_input'''
COMPRESS_SYSTEM_PROMPT = '''You are an efficient large language model that trained to compress text based on provided paragraphs.'''


def openai_compress(api_key: str, content: str, max_tries: int=5, **kwargs) -> List[str]:
    client = OpenAI(api_key=api_key)
    openai_input = Template(COMPRESS_USER_PROMPT).substitute(user_input=content)
    temperature = kwargs.get('api_temperature', 1e-5)
    
    for try_idx in range(max_tries):
        try:
            response = client.chat.completions.create(
                model=kwargs.get('api_model', 'gpt-3.5-turbo-1106'),
                messages=[
                    {"role": "system", "content": COMPRESS_SYSTEM_PROMPT},
                    {"role": "user", "content": openai_input},
                ],
                stream=False,
                temperature=temperature,
            )
        
        except Exception as e:
            if e.__class__ == RateLimitError:
                raise e
            
            if try_idx == max_tries-1:
                raise f"OpenAI API call or json parse failed. Max tries reached. Error: {e}"
            
            logger.warning(f'OpenAI API call or json parse failed. Retrying ({try_idx+1}/{max_tries})...')
            continue
        
    return response.choices[0].message.content


def openai_compress_with_key_pool(key_pool: APIKeyPool, content_to_compress: str, task_name: str, api_response_time_limit: int):
    finish_flag = False
    while not finish_flag:        
        api_key = key_pool.get_key()
        logger.info(f"[Task {task_name}] API key aquired: {api_key}")
        
        try:
            response_time_start = time.perf_counter()
            output = openai_compress(api_key, content_to_compress)
            response_time_end = time.perf_counter()
            response_time = response_time_end - response_time_start
            logger.debug(f"compressed: {output}")
            
            if response_time > api_response_time_limit:
                logger.info(f"Response time too long: {response_time}")
                key_pool.pending_key(api_key)
                
        except RateLimitError:
            logger.info(f"[Task {task_name}] Rate limit error with API key: {api_key}, removing key.")
            key_pool.remove_key(api_key)
            continue
        
        except NoAvailableAPIKey:
            logger.error(f"[Task {task_name}] No available API key, terminating task.")
            raise
        
        except Exception as e:
            res = {
                'task_name': task_name,
                'api_key':api_key,
                'input': content_to_compress,
                'output': e,
                'response_time': response_time,
                'success': 0
            }
            finish_flag = True
            logger.info(f"[Task {task_name}] Task end with error: {e}")

        res = {
            'task_name': task_name,
            'api_key':api_key,
            'input': content_to_compress,
            'output': output,
            'response_time': response_time,
            'success': 1
        }
        finish_flag = True
        logger.info(f"[Task {task_name}] Task finished successfully.")
        
    return res