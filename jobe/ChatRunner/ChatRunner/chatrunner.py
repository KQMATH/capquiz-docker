# (C) 2025: Jonas Julius Harang, Hans Georg Schaathun <hasc@ntnu.no>

"""
This is the main library, defining the classes and auxiliary
function for ChatRunner.
"""

import subprocess, base64, json, re, os
import requests
import argparse

def dumpResponse(svar,svar_fetched):
    testResults = []

    for test in json.loads(svar_fetched):
        try:
          test_obj = Test(testName=test.get( "testName", "Unnamed test" ))
        except Exception as e:
            print(test)
            raise(e)
        test_obj.addResult("mark", 1)
        for k,v in test.items():
             if k == 'iscorrect':
                test_obj.pass_test(v)
             elif k == "testName":
                continue
             else:
                test_obj.addResult(k,v)
        testResults.append(test_obj)

    svardata = Test(testName="svardata")
    svardata.addResult("gpt_svar", json.dumps(svar))
    return svardata, testResults

def formatAnswer(response,sandbox={},debug=False):
    """
    Extract the answer from the AI response.
    """
    api = sandbox.get( "API", "ollama" ).lower()
    svar = response.json()
    if api in [ "openai", "openapi" ]:
       svar = svar[ "choices"][0]
       if debug: print( "== Using OpenAPI" )
    if debug:
        print( "==svar==" )
        print(svar)
    svar = svar["message"]["content"]
    if debug:
       print( "==svar==2==" )
       print(svar)

    svar_fetched = re.search(r"\[.*\]", svar, flags=re.DOTALL).group(0)
    if debug:
        print( "==fetched==" )
        print(svar_fetched)
    return svar, svar_fetched

def chatRequest(sandbox,prompt,ans):
    """
    Make the request to the LLM, using connection parameters
    from sandbox, and the given prompt and student answer ans.
    The return value is that produced by requests.request().
    """
    if sandbox is None:
        sandbox = {}
    openai_url = sandbox.get("url", "https://api.openai.com/v1/chat/completions")
    headers = { "Content-Type": "application/json" }
    if 'OPENAI_API_KEY' in sandbox:
         headers["Authorization"] = f"Bearer {sandbox['OPENAI_API_KEY']}"
    data = { 
             "model": sandbox.get( 'model', "gpt-4o" ),
             "format" : "json",
             "stream" : False,
             "messages": [ { "role": "assistant", "content": prompt },
                         { "role": "user", "content": ans } ]
           }
    return requests.post(openai_url, headers=headers, json=data)

class Test:
   """
   A `Test` object represents a single test assessed by the AI.
   It is used as the main constituent element in the `TestResults`
   class.
   """
   def __init__(self, testName=None):
      self.result = {"name": testName, "passed": False}

   def addResult(self, field_name, field_data):
      """
      Add resultdata. Data has a key (field_name) and value (field_data)
      """
      self.result.update({field_name: field_data})

   def addResults(self, res_dict):
      for k, v in res_dict.items():
         self.addResult(k,v)

   def pass_test(self, passed):
      self.result["passed"] = passed

   def __str__(self):
      return json.dumps(self.result, indent=4)

   def __repr__(self):
      return json.dumps({"Testobject": self.result})

   def load(self, str_repr):
      try:
         obj = json.loads(str_repr)
         self.result = obj["Testobject"]
         return True
      except:
         return False

   def dump(self):
      return self.__repr__()
   def formatResult(self):
      result = self.result
      feedback = False
      if result["passed"]:
            color = "Lime"
      elif "resultat" in result.keys():
            color = "Red"
      else: return None
      return ( f'<h2 style="background-color:{color};">{result["name"]}</h2>'
           + f'\n<p>{result["resultat"]} </p>' )


class TestResults:
   def __init__(self, output, exitCode=0, name=None):
      """
      output: Output fra testprogram
      exitCode: 0: OK, 1: Feil/kræsj, 2: timeout, -1: Ingen tester å kjøre, -2: Testnummer finnes ikke
      name: this is never used in practice
      """
      self.testresults = []
      self.output = output
      self.other_output = ""
      self.exitCode = exitCode
      self.frac = 0
      self.name = name
      self.tableHeader = None
      self.tableRemap = None
      self.resultstable = None
      if exitCode != 0:
         self.results = { "failed":
              { "description": "CodeTester ran without loaded tests" } }
         return

      test = Test()
      for line in output.splitlines():
         if test.load(line):
            self.testresults.append(test)
            test = Test()
         else:
            self.other_output+= line+"\n"
      self.numTests = len(self.testresults)

   def finalise(self,debug=False):
      """
      Finalise the TestResults object, running makeResultTable()
      and mark().
      """
      if debug:
          print( "=== testResults ===" )
          print( self.contents() )

      tableRemap = {"iscorrect": "passed",
                  "Test": "name",
                  "Beskrivelse": "description"}
      tableHeader = ["iscorrect", "Test", "Beskrivelse"]
    
      self.makeResultTable(tableHeader,tableRemap)
      self.mark()
      if debug:
          print( "=== testResults (marked) ===" )
          print( self.contents() )
      # Format results
      return self
   def makeResultTable(self, tableHeader, tableRemap):
      """
      This function creates the `resultstable` attribute by
      formatting the test results
      """
      self.tableHeader = tableHeader
      self.resultstable = [tableHeader]

      if not tableRemap:
         tableRemap = {k:k for k in tableHeader}
      else:
         for header in tableHeader:
            if header not in tableRemap.keys():
               tableRemap.update({header:header})

      self.tableRemap = tableRemap
      i = 1
      for test in self.testresults:
         print( f"> test {i}" )
         print(test)
         i += 1

         row = []
         for column in self.tableHeader:
            try:
               row.append(test.result[tableRemap[column]])
            except:
               row = []
               break
         print( i, row )
         if row != []:
            self.resultstable.append(row)

   def contents(self):
      """
      Return the contents of the TestResults as a dictionary.
      """
      return  { "TestResultsObj": {
            "testresults": self.testresults,
            "other_output": self.other_output,
            "tableHeader": self.tableHeader,
            "tableRemap": self.tableRemap,
            "resultstable": self.resultstable,
            "frac": self.frac,
            "name": self.name
         }
      }
   def __repr__(self):
      """
      Return the contents of the TestResults as a string.
      """
      contents = self.contents()
      contents["testresults"] = [ t.dump() for t in contents["testresults"] ]
      return json.dumps(contents)

   def dump(self):
      """
      Return the contents of the TestResults as a string.
      """
      return self.__repr__()

   def load(self, str_repr):
      obj_read = False
      self.unencoded = ""
      for line in str_repr:
         try:
            data = json.loads(line)
            obj = data["TestResultsObj"]
            self.testresults = [Test() for res in obj["testresults"]]
            self.testresults = list(map(Test.load, self.testresults))
            self.other_output = obj["other_output"]
            self.tableHeader = obj["tableHeader"]
            self.tableRemap = obj["tableRemap"]
            self.resultstable = obj["resultstable"]
            self.frac = obj["frac"]
            self.name = obj["name"]
            obj_read = True
         except:
            self.unencoded += line + '\n'
      return obj_read

   def mark(self):
      total_marks = 0
      obtained_marks = 0
      for test in self.testresults:
         if "mark" in test.result.keys():
            mark = test.result["mark"]
            total_marks += mark
         else:
            mark = 0
         if test.result["passed"]:
            obtained_marks += mark
      if total_marks != 0:
         self.frac = obtained_marks/total_marks
      else:
         self.frac = 0

   def getCodeRunnerResult(self,
                           prehtml=None,
                           graderstate=None,
                           other_lines=False ):
       """
       Return the test results as a dict suitable for JSON export
       in the format used by CodeRunner.
       """
       if other_lines:
         prehtml = f"""<h2> Other output / error-messages from testgrader </h2>
         <p><br>
         """+self.other_output.replace("\n", "<br>")+"""
         </p></br>"""
       obj = { "fraction": self.frac,
               "testresults": self.resultstable,
               "prologuehtml": prehtml,
               "epiloguehtml": self.phtml(),
               "graderstate": graderstate }
       return obj
   def getCodeRunnerOutput(self,
                           prehtml=None,
                           graderstate=None,
                           other_lines=False ):
       """
       Return the test results as used by CodeRunner.
       This is string representation of a JSON object.
       """
       obj = self.getCodeRunnerResult(
               prehtml,graderstate,other_lines)
       return json.dumps( obj, ensure_ascii=False )
   def mergeResults(self, merging_result):
      if self.resultstable == None:
         if merging_result.resultstable == None:
            pass
         else:
            self.resultstable=merging_result.resultstable
            self.tableHeader = merging_result.tableHeader
            self.tableRemap = merging_result.tableRemap
      elif merging_result.resultstable == None:
         pass
      else:
         self.resultstable = self.resultstable + merging_result.resultstable[1:]

      self.other_output += merging_result.other_output
      self.testresults = self.testresults+merging_result.testresults
   def phtml(self):
       rl = [ test.formatResult() for test in self.testresults ]
       return rl

def getfn(fn):
    dir = os.path.dirname(os.path.abspath(__file__))
    return( os.path.join( dir, fn ) )


class CodeGrader:
   """
   The CodeGrader object is defines a test.  It can be instantiated
   with a porticular test program.  The `runTest()` method runs the test
   and returns a TestResults object.
   """
   def __init__(self,test_programs):
      if type(test_programs) == list:
         self.test_programs = test_programs
      else:
         self.test_programs = [test_programs]

   def runTest(self, num=0, timeout=1.0):
      """
      Run test program no. num, catching exceotions.  
      It produces a `TestResults` object, incorporating the test results,
      or appropriate error codes if the program fails.
      """

      if not self.test_programs:
         return TestResults(None, -1)

      if num >= len(self.test_programs):
         return TestResults(None,-2)

      try:
         with open("code.py", "w") as fout:
             fout.write(self.test_programs[num])
         sp = subprocess.run(['python3', 'code.py'],
             stderr = subprocess.STDOUT,
             universal_newlines=False,
             timeout=timeout,
             stdout=subprocess.PIPE )
         output = sp.stdout.decode()
         return TestResults(output)
      except subprocess.CalledProcessError as e:
         output = e.stdout.decode()
         return TestResults(output, exitCode=1)
      except subprocess.TimeoutExpired as e:
         output = e.stdout
         if output:
            output= output.decode()
         else:
             output = "Ingen output fra testprogrammet"
         return TestResults(output, exitCode=2)

def getPrompt(problem,literatur,gs,mdfn=getfn("prompt.md")):
    try:
       prevans = gs[ "studans" ][-1]
    except:
       prevans = "Ingen tidligere svar gitt"

    with open(mdfn, 'r') as file:
        prompt = file.read()
    prompt = prompt.format( problem=problem,
                            literatur=literatur,
                            prevans=prevans,
                           )
    return prompt

def loadtestprogram(ans,problem,literatur,gs,sandbox={},
                    pyfn="testprogram.py.txt",mdfn="prompt.md"):
    dir = os.path.dirname(os.path.abspath(__file__))
    mdfn = os.path.join( dir, mdfn )
    pyfn = os.path.join( dir, pyfn )

    prompt = getPrompt(problem,literatur,gs,mdfn=mdfn)

    with open(pyfn, 'r') as file:
        prg = file.read()
    return prg.format( prompt=prompt, studans=ans, sandbox=sandbox )

def getGraderstate(gs,studans):
    # Interpret graderstate
    step = 0
    if (not gs in ['null', '""', "''", '', '[]']):
       graderstate = json.loads(gs)
       step = graderstate["step"]
       graderstate["studans"].append(studans)
    else:
       graderstate = {"step": 0, "studans": [studans], "svar": []}
    return graderstate

def runAnswer(problem,studans,literatur={},gs="",sandbox={},qid=0,debug=False):
    """
    Run the CodeGrader, with pre- and post-processing of data.
    """

    graderstate = getGraderstate(gs,studans)

    test_program = loadtestprogram(
            studans,
            problem,
            literatur,
            graderstate,
            sandbox=sandbox,
            pyfn="testprogram.py.txt",
            mdfn="prompt.md")

    # Instantiate and run test
    test = CodeGrader([test_program])
    if debug: print( test )

    testResults = test.runTest(num=0, timeout=40.0)
    testResults.finalise(debug=debug)

    i = 1
    for test in testResults.testresults:
       if test.result["name"] == "svardata":
          graderstate["svar"].append(test.result["gpt_svar"])
       if debug:
         print( f"=> test {i}" )
         print(test)
         i += 1

    graderstate["step"] += 1

    # Format feedback for display
    if debug:
        print( "=runAnswer in debug mode=" )
        return testResults.getCodeRunnerResult(
          other_lines=True,
          graderstate=graderstate)
    else:
       return testResults.getCodeRunnerOutput(
          other_lines=True,
          graderstate=graderstate)

def testProgram(problem,studans,literatur={},gs="",sandbox={},qid=0):
    """
    This function is supposed to be functionally identical to
    `runAnswer()` without using the sandbox.  The code from 
    the test program is integrated, with additional debug output.

    In general, this function should be used to test the functionality 
    and the language models from the command line.
    """

    if sandbox is None:
        raise Exception( "No sandbox provided" )

    graderstate = getGraderstate(gs,studans)
    prompt = getPrompt(problem,literatur,gs)
    response = chatRequest(sandbox,studans,prompt)
    svar, svar_fetched = formatAnswer(response,sandbox,debug=True)

    svardata, testResults = dumpResponse( svar, svar_fetched )

    print( "==== svardata ====" )
    print(svardata)

    i = 1
    for test in testResults:
       print( f"==== test {i} ====" )
       print(test)
       i += 1
    output = svardata.dump() + "\n".join( [ x.dump() for x in testResults ] )
    testResults = TestResults(output)
    testResults.finalise()


    for test in testResults.testresults:
       if test.result["name"] == "svardata":
          graderstate["svar"].append(test.result["gpt_svar"])

    graderstate["step"] += 1

    # Format feedback for display
    return testResults.getCodeRunnerOutput(
        other_lines=True,
        graderstate=graderstate)

