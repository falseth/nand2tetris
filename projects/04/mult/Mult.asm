// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
//
// This program only needs to handle arguments that satisfy
// R0 >= 0, R1 >= 0, and R0*R1 < 32768.

// Put your code here.

@I
M=0

@N
M=0

(LOOP)
@R1
D=M
@I
D=D-M
@DONE
D;JLE

@N
D=M
@R0
D=D+M
@N
M=D

@I
M=M+1

@LOOP
0;JMP

(DONE)
@N
D=M
@R2
M=D

(EXIT)
@EXIT
0;JMP