import sys
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


# Iterates over every VM command in the file and breaks each one down
# into their fields.
class Parser:
    def __init__(self, filename):
        self.file = open(filename)
    
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
                else: # Arithmetic and Logical Command
                    self.commandType = CommandType.C_ARITHMETIC
                
                return True
                    
    def __del__(self):
        self.file.close()


# Translates each VM command into multiple assembly commands that executes the
# expected behavior and adds them to an output file.
class Translator:
    def __init__(self, filename):
        # Filename, without extension.
        self.filename = filename.split('.')[0].split('/')[-1]
        self.file = open(filename, 'w')
        # Used in writeArithmetic() as a unique counter for logical operations
        self.count = 0

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

        # Pops the argument(s) from the stack: R13=arg1 and R14=arg2
        numOfArgs = Translator.C_ARITHMETIC_DESC[command][0]
        if numOfArgs == 2: # 2 Arguments
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
        else: # 1 Argument
            self.file.write('@SP\n')
            self.file.write('AM=M-1\n')
            self.file.write('D=M\n')
            self.file.write('@R13\n')
            self.file.write('M=D\n')

        # D = f(arguments)
        cType = Translator.C_ARITHMETIC_DESC[command][1]
        code = Translator.C_ARITHMETIC_DESC[command][2]
        if numOfArgs == 1: # Unary commands
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
    def writePush(self, segment, index):
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
        elif segment == 'static': # D = *(filename.Index)
            self.file.write(f'@{self.filename}.{index}\n')
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
    def writePop(self, segment, index):
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
        elif segment == 'static': # D = filename.Index
            self.file.write(f'@{self.filename}.{index}\n')
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

    def __del__(self):
        self.file.close()


# Description: Translates the given VM file into Hack assembly file.
# Usage: python VMTranslator.py <VMfile.vm>
# Output: VMfile.asm
def main():
    inputFilename = sys.argv[1]
    outputFilename = inputFilename.split('.')[0] + '.asm'
    p = Parser(inputFilename)
    t = Translator(outputFilename)

    # This is where the translation happens.
    while p.advance():
        if p.commandType == CommandType.C_ARITHMETIC:
            t.writeArithmetic(p.command)
        elif p.commandType == CommandType.C_PUSH:
            t.writePush(p.arg1, p.arg2)
        elif p.commandType == CommandType.C_POP:
            t.writePop(p.arg1, p.arg2)
        else:
            raise Exception("Invalid command type is given by the parser!")


if __name__ == '__main__':
    main()
