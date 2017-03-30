# How to Contribute a Testcase

The online judge system supports four different kinds of test assertions:

* `success_compile`: The test is passed if the compiler successfully compiles the program.
* `failure_compile`: The test is passed if the compiler reports compilation error.
* `exitcode`: First, the compiler should successfully compiles the program. Then, the system will run the compiled program. If it terminates with the exitcode equal to the expected one, then the test is passed. Otherwise, the test is failed or timed out.
* `runtime_error`: Similar to `exitcode` assertion. The test is passed if a runtime error occured.
* `output`: Similar to `exitcode` assertion. The test is passed if the compiled program successfully terminates with outputs equal to the expected ones.

A testcase file starts with the testing program code. Then, there are several metadata to specify. To mark the start of metadata, use a line: `/*!! metadata:`. As you can imagine, the metadata region ends with a line: `!!*/`. You should make sure that no more program code after the metadata region, i.e., `!!*/` should be followed by empty newlines and EOF.

Each item of metadata is a key-value pair. Use `=== key ===` to specify a key. Values are the following lines after the key line. Here are the descriptions of required metadata:

* `comment`: Description of the testcase. Make it helpful. State tricky parts. This will be available to everyone on the website.
* `assert`: Which assertions of the four is this testcase using?
* `phase`: When should this testcase run? There are 6 phases:
    * `semantic pretest` / `semantic extended`
    * `codegen pretest` / `codegen extended`
    * `optim pretest` / `optim extended`
* `is_public`: Can people download this testcase? `True` / `False`.
* `timeout`: If the assertion is `exitcode` and `output`, you need to specify the time limit for the compiled program in seconds.
* `input`: If the assertion is `exitcode` and `output`, you need to specify the input to the compiled program. If the program does not read, simply leave the value empty.
* `exitcode`: If the assertion is `exitcode`, you need to specify the expected exitcode.
* `output`: If the assertion is `output`, you need to specify the expected output.

You can find some examples [here](https://github.com/abcdabcd987/acm-compiler-judge/tree/master/docs/demo_testcases).
