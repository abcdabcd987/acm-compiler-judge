# How to Use the Online Judge

1. Create a **private** repository at [BitBucket](https://bitbucket.org/).
2. In the project settings, find *User and group access* tab. Grant read permission to `acmcompiler` user.
3. Tell TA the URL to your git repository.
4. Make sure the following bash scripts are in the root directory of your repository:
    * `build.bash`
    * `semantic.bash`, `codegen.bash`, `optim.bash`
5. Every time you pushed your git repository, the system will automatically build your compiler, and then run tests.

If the system finds that there is a new version of your compiler (i.e. new commit in your git repository), it will download your latest code and build it. Your `build.bash` will be run when the system is building your compiler. You can download and install software that your compiler depends, and compile your compiler. Everything happened during this building process will be preserved. The source code of your compiler is placed at `/compiler/` directory.

If your compiler is built successfully, the system will test your compiler next. Tests are divided into several phases:

* `semantic pretest`
* `semantic extended`
* `codegen pretest`
* `codegen extended`
* `optim pretest`
* `optim extended`

The system will not run tests of next phase unless you have already passed all tests in the previous phase. When the system starts to run a testcase on your compiler, it will run the corresponding bash script (`semantic.bash` / `codegen.bash` / `optim.bash`). The source code will be fed to your compiler through `stdin`. Your compiler should output the target code to `stdout`.

Notice that the system runs your bash script, not directly your compiler. This means that things can be very flexible. For example, if your compiler uses file input and output, you can use the bash script to save `stdin` to a file, run your compiler, and finally print the target code to `stdout`. Like this:

```bash
cat > program.txt                  # save everything in stdin to program.txt
mycompiler program.txt target.txt  # run my compiler, save to target.txt
cat target.txt                     # print target.txt to stdout
```

Additionally, you can print some messages to `stderr`. This might be helpful when you are debugging. However, please do not print the testcase itself to `stderr`, as it will leak the testcase. And please do not try to steal non-public testcases by any means (e.g. print to `stderr`, upload to a server, etc.), which is strictly prohibited and could lead you severe punishment.
