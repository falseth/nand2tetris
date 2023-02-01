// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.

(LOOP)
@KBD
D=M
@WHITE
D;JEQ

(BLACK)

	@SCREEN
	D=M
	@LOOP
	D+1;JEQ

	@I
	M=0

	(BEGIN1)
	@I
	D=M
	@8192
	D=D-A
	@LOOP
	D;JGE

	@SCREEN
	D=A
	@I
	A=D+M
	M=-1

	@I
	M=M+1

	@BEGIN1
	0;JMP

(WHITE)

	@SCREEN
	D=M
	@LOOP
	D;JEQ

	@I
	M=0

	(BEGIN2)
	@I
	D=M
	@8192
	D=D-A
	@LOOP
	D;JGE

	@SCREEN
	D=A
	@I
	A=D+M
	M=0

	@I
	M=M+1

	@BEGIN2
	0;JMP