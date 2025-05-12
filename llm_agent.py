# coding: utf-8
import SparkApi
import os
appid = "XXXXXXXX"
api_secret = "XXXXXXXX"
api_key ="XXXXXXXX"
domain = "generalv3.5"
Spark_url = "wss://spark-api.xf-yun.com/v3.5/chat"

feedback = []
file = open("generator.py", "r")
encoder = file.read()
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
    while (getlength(text) > 8000): # Tokens Limit: 8192
        del text[0]
    return text


def fix_prompt(feedback):
    Input = f'Here is the coverage information for your generator . Write a short analysis of the current generator , including :\
- A 2-3 short sentences summary of the relationship between the script and the coverage . For example , "The script not cover part X because it generates only Y type of data ."\
- A 2-3 short sentences general guideline on how to improve the script based on the coverage information received . You don\'t need to provide a new script , just some advice on how to improve the current one.\
{ feedback }'
    question.append(checklen(getText("user",Input)))
    pass


def update_generator():
    '''
    replace the `generate_random_data` function and make the backup for the old one
    '''
    SparkApi.answer = ""
    SparkApi.main(appid,api_key,api_secret,Spark_url,domain,question)
    getText("assistant", SparkApi.answer)

    pass


if __name__ == '__main__':
    pass
