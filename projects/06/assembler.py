import sys
from enum import Enum


class CommandType(Enum):
    A_COMMAND = 1 # A-instructions: @value
    C_COMMAND = 2 # C-instructions: dest=comp;jump
    L_COMMAND = 4 # Labels: (symbol)


# Lookup Table for C-instructions' fields.
class LUT:
    dest = {
        ''   : '000',
        'M'  : '001',
        'D'  : '010',
        'MD' : '011',
        'A'  : '100',
        'AM' : '101',
        'AD' : '110',
        'AMD': '111'
    }

    jump = {
        ''   : '000',
        'JGT': '001',
        'JEQ': '010',
        'JGE': '011',
        'JLT': '100',
        'JNE': '101',
        'JLE': '110',
        'JMP': '111'
    }

    comp = {
        '0'  : '0101010',
        '1'  : '0111111',
        '-1' : '0111010',
        'D'  : '0001100',
        'A'  : '0110000',
        '!D' : '0001101',
        '!A' : '0110001',
        '-D' : '0001111',
        '-A' : '0110011',
        'D+1': '0011111',
        'A+1': '0110111',
        'D-1': '0001110',
        'A-1': '0110010',
        'D+A': '0000010',
        'D-A': '0010011',
        'A-D': '0000111',
        'D&A': '0000000',
        'D|A': '0010101',
        'M'  : '1110000',
        '!M' : '1110001',
        '-M' : '1110011',
        'M+1': '1110111',
        'M-1': '1110010',
        'D+M': '1000010',
        'D-M': '1010011',
        'M-D': '1000111',
        'D&M': '1000000',
        'D|M': '1010101'
    }


# Iterates over every assembly command in the file and breaks each one down
# into their fields.
class Parser:
    def __init__(self, filename):
        self.file = open(filename)
    
    # Gets the next assembly command in the file, sets up variables, and returns
    # True. If no more commands are found, it returns False.
    # commandType: specifies the current assembly command's type according
    #              to CommandType(Enum)
    # symbol: If commandType = A or L, it contains the symbol xxx from the
    #         A-instruction's @xxx or label declaration's (xxx), respectively.
    # dest: If commandType = C, it contains the dest field.
    # comp: If commandType = C, it contains the comp field.
    # jump: If commandType = C, it contains the jump field.
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
            else: # An assembly command.
                # Separates in-line comment, if there's any.
                command = line.split('//')[0]
                command = command.strip()

                if command[0] == '@': # A-instruction
                    self.commandType = CommandType.A_COMMAND
                    self.symbol = command[1:]
                    return True
                elif command[0] == '(': # Label declaration
                    self.commandType = CommandType.L_COMMAND
                    self.symbol = command[1:len(command)-1]
                    return True
                else: # C-instruction
                    self.commandType = CommandType.C_COMMAND

                    # Gets the dest field.
                    if '=' in command:
                        self.dest = command.split('=')[0]
                        command = command.split('=')[1]
                    else:
                        self.dest = ''
                    
                    # Gets the jump field.
                    if ';' in command:
                        self.jump = command.split(';')[1]
                        command = command.split(';')[0]
                    else:
                        self.jump = ''
                    
                    # Gets the comp field.
                    self.comp = command
                    return True
                    
    def __del__(self):
        self.file.close()


# Translates each assembly command into their binary equivalent.
class Translator:
    # Translates a C-instruction according to its comp, dest, and jump fields.
    @staticmethod
    def cTranslate(comp, dest='', jump=''):
        return ('111' + Translator.comp(comp) + Translator.dest(dest)
            + Translator.jump(jump))

    # Translates an A-instruction according to its decimal value.
    # It's equivalent to a decimal-to-binary function.
    @staticmethod
    def aTranslate(decimal):
        return '0' + format(int(decimal), 'b').rjust(15, '0')

    @staticmethod
    def dest(string):
        return LUT.dest[string]
    
    @staticmethod
    def comp(string):
        return LUT.comp[string]

    @staticmethod
    def jump(string):
        return LUT.jump[string]


# Manages all the symbols in the assembly program.
class SymbolTable:
    # Initializes the symbol table with predefined symbols.
    def __init__(self):
        self.table = {
            'SP': '0',
            'LCL': '1',
            'ARG': '2',
            'THIS': '3',
            'THAT': '4',
            'R0': '0',
            'R1': '1',
            'R2': '2',
            'R3': '3',
            'R4': '4',
            'R5': '5',
            'R6': '6',
            'R7': '7',
            'R8': '8',
            'R9': '9',
            'R10': '10',
            'R11': '11',
            'R12': '12',
            'R13': '13',
            'R14': '14',
            'R15': '15',
            'SCREEN': '16384',
            'KBD': '24576',
        }
    
    # Adds a symbol-address pair to the symbol table.
    def addEntry(self, symbol, address):
        self.table[symbol] = str(address)
    
    # Returns True if the symbol is present in the symbol table.
    # Otherwise, False.
    def contains(self, symbol):
        return symbol in self.table
    
    # Gets the address for the symbol. Should only be called if
    # contains(symbol) returns True.
    def getAddress(self, symbol):
        return self.table[symbol]


def main():
    asmFilename = sys.argv[1]
    hackFilename = asmFilename.split('.')[0] + '.hack'

    # First iteration through the file. Finds all the label declarations and
    # adds it to the symbol table.
    lineNum = 0
    sTable = SymbolTable()
    p = Parser(asmFilename)
    while p.advance():
        if p.commandType != CommandType.L_COMMAND:
            lineNum = lineNum + 1
        else:
            sTable.addEntry(p.symbol, lineNum)

    # Second iteration through the file. Translates each command into binary
    # and also manages each variable in the assembly program.
    varCount = 16
    p = Parser(asmFilename)
    with open(hackFilename, 'w') as f:
        while p.advance():
            if p.commandType == CommandType.A_COMMAND:
                symbol = p.symbol

                if symbol[0].isdigit(): # The symbol is a decimal number.
                    f.write(Translator.aTranslate(symbol) + '\n')
                elif sTable.contains(symbol): # The symbol is a label.
                    f.write(Translator.aTranslate(
                        sTable.getAddress(symbol))+ '\n')
                else: # The symbol is a variable.
                    sTable.addEntry(symbol, varCount)
                    varCount = varCount + 1
                    f.write(Translator.aTranslate(
                        sTable.getAddress(symbol)) + '\n')
            elif p.commandType == CommandType.C_COMMAND:
                f.write(Translator.cTranslate(p.comp, p.dest, p.jump) + '\n')

if __name__ == '__main__':
    main()
