import sys
from pathlib import Path
from enum import IntEnum, auto

class CommandType(IntEnum):
    C_ARITHMETIC = auto() # Arithmetic and Logical commands
    C_PUSH       = auto() # Push commands
    C_POP        = auto() # Pop commands
    C_LABEL      = auto() # Label declarations
    C_GOTO       = auto() # Unconditional jumps
    C_IF         = auto() # Conditional jumps
    C_FUNCTION   = auto() # Function declarations
    C_CALL       = auto() # Function calls
    C_RETURN     = auto() # Function returns


# Iterates over every VM command in the given VM file and breaks each one down
# into their fields.
class Parser:
    def __init__(self, file):
        self.filepath = file
        self.file = file.open()
    
    def reset(self):
        self.file = self.filepath.open()
    
    # Gets the next VM command in the file, sets up variables, and returns
    # True. If no more commands are found, it returns False.
    # commandType: specifies the current VM command's type according
    #              to CommandType(IntEnum).
    # command: the command itself
    # arg1: if any, the first argument of the command. Otherwise, None.
    # arg2: if any, the second argument of the command. Otherwise, None.
    def advance(self):
        while (True):
            line = self.file.readline()
            if line == '': # EOF has been reached.
                return False
            
            line = line.strip()
            if line == '': # An empty line.
                continue
            elif line[:2] == '//': # A full-line comment.
                continue
            else: # A VM command.
                # Separates in-line comment, if there's any.
                command = line.split('//')[0]
                command = command.strip()

                fields = command.split()
                self.command = fields[0]

                self.arg1 = None
                self.arg2 = None
                if self.command == 'push': # Push Command
                    self.commandType = CommandType.C_PUSH
                    self.arg1 = fields[1]
                    self.arg2 = fields[2]
                elif self.command == 'pop': # Pop Command
                    self.commandType = CommandType.C_POP
                    self.arg1 = fields[1]
                    self.arg2 = fields[2]
                elif self.command == 'label': # Label declaration
                    self.commandType = CommandType.C_LABEL
                    self.arg1 = fields[1]
                elif self.command == 'goto': # Unconditional jump
                    self.commandType = CommandType.C_GOTO
                    self.arg1 = fields[1]
                elif self.command == 'if-goto': # Conditional jump
                    self.commandType = CommandType.C_IF
                    self.arg1 = fields[1]
                elif self.command == 'function': # Function declaration
                    self.commandType = CommandType.C_FUNCTION
                    self.arg1 = fields[1]
                    self.arg2 = fields[2]
                elif self.command == 'call': # Function call
                    self.commandType = CommandType.C_CALL
                    self.arg1 = fields[1]
                    self.arg2 = fields[2]
                elif self.command == 'return': # Function return
                    self.commandType = CommandType.C_RETURN
                else: # Arithmetic and Logical Command
                    self.commandType = CommandType.C_ARITHMETIC
                
                return True
                    
    def __del__(self):
        self.file.close()


# Translates each VM command into multiple assembly commands that executes the
# expected behavior and adds them to the given output file.
class Translator:
    def __init__(self, file):
        self.file = file.open('w')
        # Filename, without extension. Used for 
        self.filename = file.stem
        # Used to generate unique labels throughout the ASM file.
        self.count = 0

    # Writes the bootstrap code.
    # It initializes the stack to RAM[256] and calls Sys.init
    def writeInit(self, callSysinit=True):
        self.file.write('// bootstrap code\n')

        # SP = 256
        self.file.write('@256\n')
        self.file.write('D=A\n')
        self.file.write('@SP\n')
        self.file.write('M=D\n')

        # call Sys.init
        if callSysinit:
            self.writeCall('Sys.init', '0')

    # Describes each C_ARITHMETIC VM command for use in writeArithmetic().
    # The tuple: (number of arguments, arithmetic/logical, its defining code).
    C_ARITHMETIC_DESC = {
        'add': (2, 'arithmetic', '+'),
        'sub': (2, 'arithmetic', '-'),
        'neg': (1, 'arithmetic', '-'),
        'eq' : (2, 'logical'   , 'JEQ'),
        'gt' : (2, 'logical'   , 'JGT'),
        'lt' : (2, 'logical'   , 'JLT'),
        'and': (2, 'arithmetic', '&'),
        'or' : (2, 'arithmetic', '|'),
        'not': (1, 'arithmetic', '!'),
    }

    # Translates arithmetic and logical commands.
    def writeArithmetic(self, command):
        self.file.write(f'// {command}\n')

        # Pop the argument(s) from the stack: R13=arg1 and R14=arg2
        numOfArgs = Translator.C_ARITHMETIC_DESC[command][0]
        if numOfArgs == 2:
            self.file.write('@SP\n')
            self.file.write('AM=M-1\n')
            self.file.write('D=M\n')
            self.file.write('@R14\n')
            self.file.write('M=D\n')
        self.file.write('@SP\n')
        self.file.write('AM=M-1\n')
        self.file.write('D=M\n')
        self.file.write('@R13\n')
        self.file.write('M=D\n')

        # D = f(arguments)
        cType = Translator.C_ARITHMETIC_DESC[command][1]
        code = Translator.C_ARITHMETIC_DESC[command][2]
        if numOfArgs == 1: # Unary commands: 'neg' and 'not'
            self.file.write('@R13\n')
            self.file.write('D=M\n')
            self.file.write(f'D={code}D\n')
        elif cType == 'arithmetic': # Binary arithmetic commands
            self.file.write('@R13\n')
            self.file.write('D=M\n')
            self.file.write('@R14\n')
            self.file.write(f'D=D{code}M\n')
        elif cType == 'logical': # Logical commands
            self.file.write('@R13\n')
            self.file.write('D=M\n')
            self.file.write('@R14\n')
            self.file.write(f'D=D-M\n')
            self.file.write(f'@TRUE{self.count}\n')
            self.file.write(f'D;{code}\n')
            self.file.write('D=0\n')
            self.file.write(f'@END{self.count}\n')
            self.file.write('0;JMP\n')
            self.file.write(f'(TRUE{self.count})\n')
            self.file.write('D=-1\n')
            self.file.write(f'(END{self.count})\n')

            self.count = self.count + 1
        else:
            raise Exception('Invalid command passed into writeArithmetic()!')

        # *SP = D
        self.file.write('@SP\n')
        self.file.write('A=M\n')
        self.file.write('M=D\n')
        
        # SP++
        self.file.write('@SP\n')
        self.file.write('M=M+1\n')
    
    # Translates push commands.
    def writePush(self, segment, index, sourcefile=None):
        self.file.write(f'// push {segment} {index}\n')

        # D = *(Segment+Index)
        if segment == 'local':
            self.file.write('@LCL\n')
            self.file.write('D=M\n')
            self.file.write(f'@{int(index)}\n')
            self.file.write('A=D+A\n')
            self.file.write('D=M\n')
        elif segment == 'argument':
            self.file.write('@ARG\n')
            self.file.write('D=M\n')
            self.file.write(f'@{int(index)}\n')
            self.file.write('A=D+A\n')
            self.file.write('D=M\n')
        elif segment == 'this':
            self.file.write('@THIS\n')
            self.file.write('D=M\n')
            self.file.write(f'@{int(index)}\n')
            self.file.write('A=D+A\n')
            self.file.write('D=M\n')
        elif segment == 'that':
            self.file.write('@THAT\n')
            self.file.write('D=M\n')
            self.file.write(f'@{int(index)}\n')
            self.file.write('A=D+A\n')
            self.file.write('D=M\n')
        elif segment == 'constant': # D = constant
            self.file.write(f'@{int(index)}\n')
            self.file.write('D=A\n')
        elif segment == 'static': # D = *(sourcefilename.Index)
            self.file.write(f'@{sourcefile.stem}.{index}\n')
            self.file.write('D=M\n')
        elif segment == 'pointer': # D = *(3+Index)
            self.file.write(f'@{3 + int(index)}\n')
            self.file.write('D=M\n')
        elif segment == 'temp': # D = *(5+Index)
            self.file.write(f'@{5 + int(index)}\n')
            self.file.write('D=M\n')
        else:
            raise Exception('Invalid segment is passed into writePush()!')

        # *SP = D
        self.file.write('@SP\n')
        self.file.write('A=M\n')
        self.file.write('M=D\n')

        # SP++
        self.file.write('@SP\n')
        self.file.write('M=M+1\n')
        
    # Translates pop commands.
    def writePop(self, segment, index, sourcefile=None):
        self.file.write(f'// pop {segment} {index}\n')

        # R13 = Segment + Index
        if segment == 'local':
            self.file.write('@LCL\n')
            self.file.write('D=M\n')
            self.file.write(f'@{index}\n')
            self.file.write('D=D+A\n')
            self.file.write('@R13\n')
            self.file.write('M=D\n')
        elif segment == 'argument':
            self.file.write('@ARG\n')
            self.file.write('D=M\n')
            self.file.write(f'@{index}\n')
            self.file.write('D=D+A\n')
            self.file.write('@R13\n')
            self.file.write('M=D\n')
        elif segment == 'this':
            self.file.write('@THIS\n')
            self.file.write('D=M\n')
            self.file.write(f'@{index}\n')
            self.file.write('D=D+A\n')
            self.file.write('@R13\n')
            self.file.write('M=D\n')
        elif segment == 'that':
            self.file.write('@THAT\n')
            self.file.write('D=M\n')
            self.file.write(f'@{index}\n')
            self.file.write('D=D+A\n')
            self.file.write('@R13\n')
            self.file.write('M=D\n')
        elif segment == 'static': # D = sourcefilename.Index
            self.file.write(f'@{sourcefile.stem}.{index}\n')
            self.file.write('D=A\n')
            self.file.write('@R13\n')
            self.file.write('M=D\n')
        elif segment == 'pointer': # D = 3 + Index
            self.file.write(f'@{3 + int(index)}\n')
            self.file.write('D=A\n')
            self.file.write('@R13\n')
            self.file.write('M=D\n')
        elif segment == 'temp': # D = 5 + Index
            self.file.write(f'@{5 + int(index)}\n')
            self.file.write('D=A\n')
            self.file.write('@R13\n')
            self.file.write('M=D\n')
        else:
            raise Exception('Invalid segment is passed into writePop()!')

        # D = *(--SP)
        self.file.write('@SP\n')
        self.file.write('AM=M-1\n')
        self.file.write('D=M\n')

        # *R13 = D
        self.file.write('@R13\n')
        self.file.write('A=M\n')
        self.file.write('M=D\n')

    # Translates label declarations.
    def writeLabel(self, label, functionName):
        self.file.write(f'// label {label}\n')

        self.file.write(f'({functionName}${label})\n')

    # Translates uncoditional jumps.
    def writeGoto(self, label, functionName):
        self.file.write(f'// goto {label}\n')

        self.file.write(f'@{functionName}${label}\n')
        self.file.write('0;JMP\n')

    # Translates conditional jumps.
    def writeIf(self, label, functionName):
        self.file.write(f'// if-goto {label}\n')

        # D = *(--SP)
        self.file.write('@SP\n')
        self.file.write('AM=M-1\n')
        self.file.write('D=M\n')

        # Jump if D != 0, else continue
        self.file.write(f'@{functionName}${label}\n')
        self.file.write('D;JNE\n')

    # Translates function declarations.
    def writeFunction(self, functionName, numLocals):
        self.file.write(f'// function {functionName} {numLocals}\n')

        # Function entry label declaration.
        self.file.write(f'({functionName})\n')

        # Initialize all local variables to 0.
        self.file.write('@LCL\n')
        self.file.write('A=M\n')
        for i in range(int(numLocals)):
            self.file.write('M=0\n')
            self.file.write('A=A+1\n')
        
        # Initialize SP
        self.file.write('D=A\n')
        self.file.write('@SP\n')
        self.file.write('M=D\n')

    # Translates function calls.
    def writeCall(self, functionName, numArgs):
        self.file.write(f'// call {functionName} {numArgs}\n')     
        
        # Push return_address
        self.file.write(f'@ret_add{self.count}\n')
        self.file.write('D=A\n')
        self.file.write('@SP\n')
        self.file.write('A=M\n')
        self.file.write('M=D\n')
        self.file.write('@SP\n')
        self.file.write('M=M+1\n')
        
        # Push LCL
        self.file.write('@LCL\n')
        self.file.write('D=M\n')
        self.file.write('@SP\n')
        self.file.write('A=M\n')
        self.file.write('M=D\n')
        self.file.write('@SP\n')
        self.file.write('M=M+1\n')
        
        # Push ARG
        self.file.write('@ARG\n')
        self.file.write('D=M\n')
        self.file.write('@SP\n')
        self.file.write('A=M\n')
        self.file.write('M=D\n')
        self.file.write('@SP\n')
        self.file.write('M=M+1\n')
        
        # Push THIS
        self.file.write('@THIS\n')
        self.file.write('D=M\n')
        self.file.write('@SP\n')
        self.file.write('A=M\n')
        self.file.write('M=D\n')
        self.file.write('@SP\n')
        self.file.write('M=M+1\n')
        
        # Push THAT
        self.file.write('@THAT\n')
        self.file.write('D=M\n')
        self.file.write('@SP\n')
        self.file.write('A=M\n')
        self.file.write('M=D\n')
        self.file.write('@SP\n')
        self.file.write('M=M+1\n')
        
        # ARG = SP-(N+5)
        self.file.write('@SP\n')
        self.file.write('D=M\n')
        self.file.write(f'@{int(numArgs)+5}\n')
        self.file.write('D=D-A\n')
        self.file.write('@ARG\n')
        self.file.write('M=D\n')

        # LCL = SP
        self.file.write('@SP\n')
        self.file.write('D=M\n')
        self.file.write('@LCL\n')
        self.file.write('M=D\n')
        
        # goto f
        self.file.write(f'@{functionName}\n')
        self.file.write('0;JMP\n')
         
        # (return_address)
        self.file.write(f'(ret_add{self.count})\n')

        self.count = self.count + 1

    # Translates function returns.
    def writeReturn(self):
        self.file.write('// return\n')

        # FRAME = LCL
        self.file.write('@LCL\n')
        self.file.write('D=M\n')
        self.file.write('@R13\n')
        self.file.write('M=D\n')

        # RET = *(FRAME-5)
        # We save the return value because it might get overwritten
        # when numArgs = 0.
        self.file.write('@5\n')
        self.file.write('A=D-A\n')
        self.file.write('D=M\n')
        self.file.write('@R14\n')
        self.file.write('M=D\n')

        # *ARG = pop()
        self.file.write('@SP\n')
        self.file.write('AM=M-1\n')
        self.file.write('D=M\n')
        self.file.write('@ARG\n')
        self.file.write('A=M\n')
        self.file.write('M=D\n')

        # SP = ARG+1
        self.file.write('@ARG\n')
        self.file.write('D=M+1\n')
        self.file.write('@SP\n')
        self.file.write('M=D\n')

        # THAT = *(FRAME-1)
        self.file.write('@R13\n')
        self.file.write('D=M\n')
        self.file.write('@1\n')
        self.file.write('A=D-A\n')
        self.file.write('D=M\n')
        self.file.write('@THAT\n')
        self.file.write('M=D\n')

        # THIS = *(FRAME-2)
        self.file.write('@R13\n')
        self.file.write('D=M\n')
        self.file.write('@2\n')
        self.file.write('A=D-A\n')
        self.file.write('D=M\n')
        self.file.write('@THIS\n')
        self.file.write('M=D\n')

        # ARG = *(FRAME-3)
        self.file.write('@R13\n')
        self.file.write('D=M\n')
        self.file.write('@3\n')
        self.file.write('A=D-A\n')
        self.file.write('D=M\n')
        self.file.write('@ARG\n')
        self.file.write('M=D\n')

        # LCL = *(FRAME-4)
        self.file.write('@R13\n')
        self.file.write('D=M\n')
        self.file.write('@4\n')
        self.file.write('A=D-A\n')
        self.file.write('D=M\n')
        self.file.write('@LCL\n')
        self.file.write('M=D\n')

        # goto RET
        self.file.write('@R14\n')
        self.file.write('A=M\n')
        self.file.write('0;JMP\n')

    def __del__(self):
        self.file.close()


# Description: Translates the given VM file(s) into a Hack assembly file.
#              If Sys.init is defined, then the VM will call it. Else, no.
# Input: [{file}.vm|{directory}]
# Output: [{file}.asm|{directory}.asm]
def main():
    # Invalid number of arguments given.
    if len(sys.argv) != 2:
        print('Usage: python ' + Path(__file__).name
            + ' [{file}.vm|{directory}]')
        return

    # Input given, must be a file or a directory.
    input = Path(sys.argv[1])
    if not input.exists():
        print('File or directory does not exist!')
        return
    
    if input.is_file(): # Input is a file.
        # The extension must be .vm
        if input.suffix != '.vm':
            print('The file is not an VM file!')
            return

        # Initialize Parser for the input file
        # and Translator for the output file.
        p = Parser(input)
        output = input.with_suffix('.asm')
        t = Translator(output)

        # Finds out whether Sys.init is defined or not.
        sysinitDefined = False
        while p.advance():
            if p.commandType == CommandType.C_FUNCTION and p.arg1 == 'Sys.init':
                sysinitDefined = True
                break
        p.reset()
        
        # The translation process.
        t.writeInit(sysinitDefined)
        while p.advance():
            if p.commandType == CommandType.C_ARITHMETIC:
                t.writeArithmetic(p.command)
            elif p.commandType == CommandType.C_PUSH:
                t.writePush(p.arg1, p.arg2, p.filepath)
            elif p.commandType == CommandType.C_POP:
                t.writePop(p.arg1, p.arg2, p.filepath)
            elif p.commandType == CommandType.C_LABEL:
                t.writeLabel(p.arg1, currentFunctionName)
            elif p.commandType == CommandType.C_GOTO:
                t.writeGoto(p.arg1, currentFunctionName)
            elif p.commandType == CommandType.C_IF:
                t.writeIf(p.arg1, currentFunctionName)
            elif p.commandType == CommandType.C_FUNCTION:
                currentFunctionName = p.arg1
                t.writeFunction(p.arg1, p.arg2)
            elif p.commandType == CommandType.C_CALL:
                t.writeCall(p.arg1, p.arg2)
            elif p.commandType == CommandType.C_RETURN:
                t.writeReturn()
            else:
                raise Exception("Invalid command type is given by the parser!")
        
        return
    else: # Input is a directory.
        # At least 1 VM file must exist in the directory.
        vmfiles = sorted(input.glob('*.vm'))
        if len(vmfiles) < 1:
            print('No VM file exists in the directory!')
            return
        
        # Initialize Parsers for the input files.
        parsers = []
        for vmfile in vmfiles:
            parsers.append(Parser(vmfile))
        
        # Initialize Translator for the output file.
        output = input / (input.stem + '.asm')
        t = Translator(output)

        # The current function name, used to define labels as
        # f$b where b is the label name and f is the function
        # name where b resides.
        currentFunctionName = 'boot'

        # Finds out whether Sys.init is defined or not.
        sysinitDefined = False
        for p in parsers:
            while p.advance():
                if (p.commandType == CommandType.C_FUNCTION
                    and p.arg1 == 'Sys.init'
                ):
                    sysinitDefined = True
                    break

            p.reset()

            if sysinitDefined:
                break

        # The translation process.
        t.writeInit(sysinitDefined)
        for p in parsers:
            while p.advance():
                if p.commandType == CommandType.C_ARITHMETIC:
                    t.writeArithmetic(p.command)
                elif p.commandType == CommandType.C_PUSH:
                    t.writePush(p.arg1, p.arg2, p.filepath)
                elif p.commandType == CommandType.C_POP:
                    t.writePop(p.arg1, p.arg2, p.filepath)
                elif p.commandType == CommandType.C_LABEL:
                    t.writeLabel(p.arg1, currentFunctionName)
                elif p.commandType == CommandType.C_GOTO:
                    t.writeGoto(p.arg1, currentFunctionName)
                elif p.commandType == CommandType.C_IF:
                    t.writeIf(p.arg1, currentFunctionName)
                elif p.commandType == CommandType.C_FUNCTION:
                    currentFunctionName = p.arg1
                    t.writeFunction(p.arg1, p.arg2)
                elif p.commandType == CommandType.C_CALL:
                    t.writeCall(p.arg1, p.arg2)
                elif p.commandType == CommandType.C_RETURN:
                    t.writeReturn()
                else:
                    raise Exception(
                        "Invalid command type is given by the parser!")


if __name__ == '__main__':
    main()
