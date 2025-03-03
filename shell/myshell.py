#! /usr/bin/env python3

import os, sys, re
import multiprocessing

def printPrompt():
    # display shell command prompt
    ps1 = os.getenv("PS1", "$ ")
    print(ps1, end="", flush=True)

def getExec_path(command):
    # search path on system for a command matching executable
    paths = os.getenv("PATH").split(":")
    for path in paths:
        executablePath = os.path.join(path, command)
        if os.path.exists(executablePath):
            return executablePath
    return command

def getCommands_operators(command):
    commandsSpl = command.split(' ')
    commands = []
    operators = []
    allOperators = re.compile(r'\s*([\|<>;])\s*', re.IGNORECASE)
    for each in commandsSpl:
        if allOperators.match(each):
            operators.append(each)
        else:
            commands.append(each)
    return commands, operators

def input_redirection(command, inputFile):
    if not os.path.isfile(inputFile):
        sys.stderr.write(f'Error: File not found: {filename}\n')
        return
    try:
        pid = os.fork()
        if pid == 0:
            with open(inputFile, 'r') as file:
                os.dup2(file.fileno(), sys.stdin.fileno())
                os.execve(command[0], command, os.environ)
        elif pid > 0:
            pidStatus = os.waitpid(pid, 0)
            if os.WIFEXITED(pidStatus):
                return os.WEXITSTATUS(status)
    except Exception as e:
        sys.stderr.write(f'Error: {e}')
            

def output_redirection(command, outputFile):
    try:
        pid = os.fork()
        if pid == 0:
            with open(outputFile, 'w') as file:
                os.dup2(file.fileno(), sys.stdout.fileno())
                os.execve(command[0], command, os.environ)
        elif pid > 0:
            pidStatus = os.waitpid(pid, 0)
            if os.WIFEXITED(pidStatus):
                return os.WEXITSTATUS(pidStatus)
    except Exception as e:
        print(f'Error: {e}')
    except PermissionError:
        print(f'Error: Insuffiecient permissions to write to output file {outputFile}')
        
def pipe_handler(command1, command2):
    try:
        pipeReader, pipeWriter = os.pipe()
        pid1 = os.fork()
        if pid1 == 0:
            os.dup2(pipeWriter, sys.stdout.fileno())
            os.close(pipeReader)
            os.close(pipeWriter)
            os.execve(command1[0], command1, os.environ)
        elif pid1 > 0:
            os.close(pipeWriter)
            pid2 = os.fork()
            if pid2 == 0:
                os.dup2(pipeReader, sys.stdin.fileno())
                os.close(pipeReader)
                os.execve(command2[0], command2, os.environ)
            elif pid2 > 0:
                os.close(pipeReader)
                pid1Status = os.waitpid(pid1,  0)
                pid2Status = os.waitpid(pid2, 0)
                if os.WIFEXITED(pid1Status) and os.WIFEXITED(pid2Status):
                    return os.WEXITSTATUS(pid2Status)
    except Exception as e:
        print(f'Error: {e}')

def shellCommands(command):
    execCmd, operators = getCommands_operators(command)
    if "cd" in execCmd:
        cdInd = execCmd.index("cd")

        if cdInd + 1 < len(execCmd):
            try:
                os.chdir(execCmd[cdInd+1])
                execCmd.pop(cdInd+1)
                execCmd.remove("cd")
            except FileNotFoundError:
                print("Directory not found")
        else:
                print("Format: cd <dir>")
    elif "echo" in execCmd:
        echoInd = execCmd.index("echo")
        print(" ".join(execCmd[echoInd+1:]))
        execCmd = execCmd[echoInd:]
    elif "pwd" in execCmd:
        #pwdInd = execCmd.index("pwd")
        curPWD = os.getcwd()
        print("".join(curPWD))
    else:
        try:
            pid3 = os.fork()
            if pid3 == 0:
                os.execve(getExec_path(execCmd[0]), execCmd,os.environ)
            else:
                os.waitpid(pid3, 0)
        except Exception as e:
            print(f'Error: {e}')
    #print("..")  
    for i, oper in enumerate(operators):
        if oper == '|':
            pid = os.fork()
            if pid == 0:
                pipe_handler(execCmd[i], execCmd[i+1])
            else:
                os.waitid(os.P_PID, pid, os.WEXITED)
        elif oper == '<':
            output_redirection(execCmd[i], execCmd[i+1])
        elif oper == '>':
            input_redirection(execCmd[i], execCmd[i+1])
        else:
            pid = os.fork()
            if pid == 0:
                os.execve(getExec_path(execCmd[0]), execCmd, os.environ)
            else:
                os.waitpid(pid, 0)
        
def shell():
    #curDirectory = os.getcwd()
    while True:
        printPrompt()
        userInput = sys.stdin.readline().rstrip('\n')

        if userInput == 'exit':
            sys.exit(0) # exit shell
        elif userInput == '':
            pass
        else:
            shellCommands(userInput)

if __name__ == "__main__":
    shell()
