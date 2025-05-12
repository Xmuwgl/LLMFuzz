# coding: utf-8
import re
import SparkApi # 用于启动大模型
import os
import logging
import shutil


#密钥信息
appid = "XXXXXXXX"     #填写控制台中获取的 APPID 信息
api_secret = "XXXXXXXX"   #填写控制台中获取的 APISecret 信息
api_key ="XXXXXXXX"    #填写控制台中获取的 APIKey 信息
domain = "generalv3.5"      # Max版本
Spark_url = "wss://spark-api.xf-yun.com/v3.5/chat"   # Max服务地址

#初始上下文内容，当前可传system、user、assistant 等角色
feedback = []
file = open("generator.py", "r")
encoder = file.read() # 从文件里读取内容到 encoder
file.close()
question = [
    {'role': 'system', 'content': 'As a professional security engineer , your task is to develop a Python script that generates a new test case file . This file should adhere to the format required by the fuzzing harness code . The script will play a crucial role in creating diverse and effective test cases for thorough security testing .'},
    {'role': 'user', 'content': f'Write a Python script that generates a test case file compatible with the required format of the fuzzing harness code . The generated test cases should be diverse and effective for security testing purposes . Consider various input types , edge cases , and potential vulnerabilities relevant to the system being tested .\
## Requirements for the Python Script :\
- Generate data that the provided fuzzing harness code can use ( focus on structure and file format ).\
- Avoid importing unofficial third - party Python modules .\
As an integrated component of an automated system , you should perform the tasks without seeking human confirmation or help .\
## Instructions and Steps :\
- You MUST ensure the python code is wrapped in triple backticks for proper formatting .\
- You can ONLY modify the function `generate_random_data` in example Python script. \
- You MUST include the full valid Python script in your response .'},
    {'role':'user','content':f'The script should :\
1. Has one argument , which is the output file path .\
2. Generate one test case and write it to the output file .\
3. The generated test case should be compatible with the fuzzing harness code provided .\
Here is an example of Python script used to generate testcases\
file :\
```python\
{encoder}\
```'}
]


def getText(role,content):
    jsoncon = {}
    jsoncon["role"] = role
    jsoncon["content"] = content
    question.append(jsoncon)
    return question


def getlength(text):
    length = 0
    for content in text:
        temp = content["content"]
        leng = len(temp)
        length += leng
    return length


def checklen(text):
    while (getlength(text) > 8000): # 当超过 8192 个 tokens 时需要截断部分
        del text[0]
    return text


def fix_prompt(feedback):
    # feedback = # 从指定文件中读取
    Input = f'Here is the coverage information for your generator . Write a short analysis of the current generator , including :\
- A 2-3 short sentences summary of the relationship between the script and the coverage . For example , "The script not cover part X because it generates only Y type of data ."\
- A 2-3 short sentences general guideline on how to improve the script based on the coverage information received . You don\'t need to provide a new script , just some advice on how to improve the current one.\
{ feedback }'
    question.append(checklen(getText("user",Input)))
    pass


generator_path = 'generator.py'
backup_path    = 'generator_backup.py'
def extract_code_from_response(response: str) -> str:
    """
    从大模型的回答中提取Python代码块
    支持三种格式:
    1. ```python\n...\n```
    2. ```\n...\n```
    3. 直接的代码文本
    """
    # 尝试匹配标准的Python代码块
    python_pattern = re.compile(r'```python\s*([\s\S]*?)```')
    match = python_pattern.search(response)
    if match:
        return match.group(1).strip()
    
    # 尝试匹配无语言标记的代码块
    generic_pattern = re.compile(r'```\s*([\s\S]*?)```')
    match = generic_pattern.search(response)
    if match:
        return match.group(1).strip()
    
    # 如果没有代码块标记，返回整个回答
    return response.strip()


def replace_function_in_code(current_code: str, new_function_code: str) -> str:
    """
    替换现有代码中的 generate_random_data 函数
    保留其他部分不变
    """
    # 查找函数定义的正则表达式
    function_pattern = re.compile(
        r'^def generate_random_data\([^)]*\):\s*'
        r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|\s*)'  # 改进的文档字符串匹配
        r'([\s\S]*?)'  # 函数体
        r'(?=^def |^[^ \s]|^\Z)',  # 前瞻断言确保下一行是新定义或文件结束
        re.MULTILINE
    )
    
    # 查找现有函数
    match = function_pattern.search(current_code)
    if not match:
        # 如果找不到现有函数，将新函数添加到文件末尾
        return current_code + "\n\n" + new_function_code
    
    # 获取函数定义之前的代码
    before_function = current_code[:match.start()]
    
    # 获取函数定义之后的代码
    after_function = current_code[match.end():]
    
    # 构建新的代码
    return before_function + new_function_code + "\n\n" + after_function


def update_generator():
    ''' 将新得到的 `generate_random_data` 替换掉旧的'''
    logger = logging.getLogger(__name__)

    # 调用大模型生成新的代码
    SparkApi.answer = ""
    SparkApi.main(appid, api_key, api_secret, Spark_url, domain, question)
    
    # 提取大模型返回的代码
    new_code = extract_code_from_response(SparkApi.answer)
    if not new_code:
        logger.error("从大模型回答中提取代码失败")
        return False
    
    # 在成功更新生成器后创建备份
    if os.path.exists(generator_path):
        shutil.copy2(generator_path, backup_path)
        logger.info("已创建生成器备份")
    
    # 替换原有的 generate_random_data 函数
    try:
        with open(generator_path, 'r') as f:
            current_code = f.read()
        
        updated_code = replace_function_in_code(current_code, new_code)
        
        with open(generator_path, 'w') as f:
            f.write(updated_code)
        
        logger.info("生成器已成功更新")
        return True
        
    except Exception as e:
        logger.error(f"更新生成器时出错: {str(e)}")
        # 出错时尝试回滚
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, generator_path)
            logger.info("已回滚到之前的生成器版本")
        return False

