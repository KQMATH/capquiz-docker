# CodeRunner Docker Environment

This setup is inspired by the 
[bitnami repository](https://github.com/bitnami/bitnami-docker-moodle for configuration parameters),
but the docker images have been replaced with an official database
image and a web server image from Moodle.

The purpose of this repo is to test a setup using large language
models (LLM) to provide automated feedback.  For this purpose CodeRunner
is used.  Even though CodeRunner is made for programming tasks,
it is here used only for free form text.  The programming 
features are used to pass student responses to the LLM.

Under `jobe/ChatRunner` there is a python package to provide the
API to call an LLM from CodeRunner.

## Authors

+ Jonas Julius Harang, idea and original prototype
+ Hans Georg Schaathun, refactoring and documentation for reuse and publication


## Usage in Moodle

1.  Make sure you have git, docker, and docker-compose.
2.  Run `sh gitclone.sh` to clone the Moodle directory with
    plugins required for CodeRunner.
3.  Run `docker compose up -d` to start the server.
4.  Connect to http://localhost:8080/
    + You will have to go through the setup procedure.
      In the database setup, you have to choose mariadb as
      the server type, and mariadb as the hostname.  The database
      user and password are found in the docker-compose.yml file.
    + Moodle will complain that you are not using SSL (https).  
      It still works, and for testing and prototyping there is no
      need to worry.  For production, this has to change.
5.  Configure Site Administration -> Plugins -> CodeRunner.
    Set Jobe server to «jobe».
5.  Configure Site Administration -> General -> HTTP Security.
    Prune the «cURL blocked hosts list».  It may suffice to remove
    the 172.* addresses, but this may depend on the configuration of
    docker.
6.  Run `docker exec -it moodle-coderunner-docker-moodle-1 /usr/local/bin/php  /var/www/html/admin/cli/cron.php`
    + Moodle usually requires a cron job, but cron works poorly in docker containers.  
    + You may have to rerun the above command regularly, but the critical issue is
      to run it once to have the question bank work.
    + In production it should be run from cron.


### Sample Question

To enter a sample question in CodeRunner, you can open a new question and make
the following changes.  This assumes that you have an API key with OpenAI.

1. Under CodeRunner Question type 
    + Question Type, select Python3
    + Customisation, tick Customise
2. Enter the following under CodeRunner question type -> Template params:
```
{ "API": "openai", "model": "gpt-4o", "url": "https://api.openai.com/v1/chat/completions", "OPENAI_API_KEY": "<your key>" }
```
3. Enter the contents of file `jobe/ChatRunner/chatgpt.py` under Customisation -> Template
4. Under Customisation -> Grading, select Template grader

4. Enter a time limit under Advanced Customisation -> Sandbox -> TimieLimit.
   In production you probably do not want more than 20, but for testing it may be
   useful to have, say, 180.
6. Under General, give the question a name and question text.  This does not matter
   for testing.  You can use sampel question text from `Example/problem.md` and
   «Mikroskopet» for question name.
7. Under support files, add the files from the Example directory:
   literature.json, problem.md, question.md
8. Testing the question, you may use `Example/naiveanswer.md` as a dummy answer.

Developing your own qestion, you change the files used in steps 6-8; everything else is
constant.

Using different language models, you change the sandbox parameters i Step 2.

## Testing and Developing ChatRunner

To test ChatRunner without using Moodle, you should install it using pip.
For instance, like this
```sh
python3 -m venv venv
. venv/bin/activate
pip install build
cd jobe/ChatRunner
pip install -e .
```
This installs in editable mode, so that you can keep developing and testing 
the module.

To test against OpenAI/ChatGPT, you have to get an API key, and edit
the script (under jobe/ChatRunenr) to use this key before running,
```sh
sh chatgpttest.sh
```

This is work in progress, and we have not yet been able to format the
output, which is intended to be parsed by CodeRunner, so that it is
readable for human users in the command line interface.
It is possible to add the `-T` option to run outside the sandbox, which
gives more debug information.


### Using Ollama

We have started experimenting using ollama, but this is still flaky
and unstable.

You can run ollama in docker, using
```sh
docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
docker exec -it ollama ollama pull llama3
```
This installs the llama3 model.  You can install other models as desired.

If you want to test this as a chatbot, use,
```sh
docker exec -it ollama ollama run llama3
```

To test ChatRunner against ollama, you can run 
```sh
sh ollamatest.sh
```

The main problem with ollama, is that the models available are inferior
to chatgpt and often produce syntactically unexpected output.  To make
it work in practice, two things are required
1.  Improved prompting to reduce the error frequency.
2.  Improve error handling to manage the consequences of errors.
