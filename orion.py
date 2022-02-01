import afskmodem
"""
x--------------------------------------------x
| ORION (Open Radio Inter-Operable Network)  |
| https://github.com/jvmeifert/orion         |
x--------------------------------------------x
"""
################################################################################ General utilities
class FormatUtils:
    # Parse a series of octets given in string form and of a given length (xxx.xxx.xxx.xxx)
    def parseOctets(data: str, n = 4) -> list: 
        octs = data.split(".")
        if(len(octs) < n): # default to 0.*n if undersize
            octs = ["0"] * n
        if(len(octs) > n): # ignore extra octets
            octs = octs[0:n]
    
        intOcts = []
        for i in octs:
            try:
                intOcts.append(int(i))
            except:
                intOcts.append(0)
        
        for i in range(len(intOcts)):
            if(intOcts[i] > 255):
                intOcts[i] = 255
            if(intOcts[i] < 0):
                intOcts[i] = 0
        
        return intOcts
    
    def makeOctets(data: list) -> str:
        p = ""
        for i in data:
            mi = i
            if(mi > 255):
                mi = 255
            if(mi < 0):
                mi = 0
            p += str(mi) + "."
        return p.rstrip(".")
        

    def intToBytes(data: int, n: int) -> bytes: # int to n bytes
        if(data > (256 ** n) - 1):
            data = (256 ** n) - 1
        if(data < 0):
            data = 0
        return data.to_bytes(n, "big") # network byte order

    def bytesToInt(data: bytes) -> int: # bytes to int
        return int.from_bytes(data , "big")

    def trimBytes(data, val: bytes) -> bytes: # shorten bytes object to specified length
        if(len(data) > val):
            return data[0:val]
        else:
            return data

################################################################################ Wrapper class for digital radio interface
class RadioInterface: 
    def __init__(self):
        self.receiver = afskmodem.digitalReceiver(afskmodem.digitalModulationTypes.afsk1200())
        self.transmitter = afskmodem.digitalTransmitter(afskmodem.digitalModulationTypes.afsk1200())
        self.integrity = 1

    def rx(self, timeout=-1): # Listen for and catch a transmission, report bit error rate and return data (bytes)
        rd, te = self.receiver.rx(timeout)
        if(len(rd) > 4): # Only record integrity for transmissions longer than 4 bytes
            self.integrity = 1 - (te / len(rd))
        return rd

    def tx(self, data: bytes): # Transmit raw data (bytes)
        self.transmitter.tx(data)

    def getIntegrity(self) -> float: # Return integrity of the last received transmission
        return self.integrity

# Packet structure and operations
class Packet:
    def __init__(self, data=b'', source = "0.0.0.0", dest = "0.0.0.0", sPort = 0, dPort = 0, flag = 0):
        self.source = FormatUtils.parseOctets(source)
        self.dest = FormatUtils.parseOctets(dest)
        # Source address
        self.src0 = FormatUtils.intToBytes(self.source[0], 1)
        self.src1 = FormatUtils.intToBytes(self.source[1], 1)
        self.src2 = FormatUtils.intToBytes(self.source[2], 1)
        self.src3 = FormatUtils.intToBytes(self.source[3], 1)
        # Dest address
        self.dest0 = FormatUtils.intToBytes(self.dest[0], 1)
        self.dest1 = FormatUtils.intToBytes(self.dest[1], 1)
        self.dest2 = FormatUtils.intToBytes(self.dest[2], 1)
        self.dest3 = FormatUtils.intToBytes(self.dest[3], 1)
        # Source port
        self.sPort0 = bytes([FormatUtils.intToBytes(sPort, 2)[0]])
        self.sPort1 = bytes([FormatUtils.intToBytes(sPort, 2)[1]])
        # Dest port
        self.dPort0 = bytes([FormatUtils.intToBytes(dPort, 2)[0]])
        self.dPort1 = bytes([FormatUtils.intToBytes(dPort, 2)[1]])
        # Data
        self.data = FormatUtils.trimBytes(data, 65535)
        # Params
        self.flag = FormatUtils.intToBytes(flag, 1)
        self.age = FormatUtils.intToBytes(0, 1)
        self.dlen0 = bytes([FormatUtils.intToBytes(len(self.data), 2)[0]])
        self.dlen1 = bytes([FormatUtils.intToBytes(len(self.data), 2)[1]])
        self.empty = False
    
    def isEmpty(self) -> bool:
        return self.empty
    
    def setSource(self, data: str):
        self.source = FormatUtils.parseOctets(data)
        self.src0 = FormatUtils.intToBytes(self.source[0], 1)
        self.src1 = FormatUtils.intToBytes(self.source[1], 1)
        self.src2 = FormatUtils.intToBytes(self.source[2], 1)
        self.src3 = FormatUtils.intToBytes(self.source[3], 1)
        self.empty = False
    
    def setDest(self, data: str):
        self.dest = FormatUtils.parseOctets(data)
        self.dest0 = FormatUtils.intToBytes(self.dest[0], 1)
        self.dest1 = FormatUtils.intToBytes(self.dest[1], 1)
        self.dest2 = FormatUtils.intToBytes(self.dest[2], 1)
        self.dest3 = FormatUtils.intToBytes(self.dest[3], 1)
        self.empty = False

    def setSourcePort(self, data: int):
        self.sPort0 = bytes([FormatUtils.intToBytes(data, 2)[0]])
        self.sPort1 = bytes([FormatUtils.intToBytes(data, 2)[1]])
        self.empty = False

    def setDestPort(self, data: int):
        self.dPort0 = bytes([FormatUtils.intToBytes(data, 2)[0]])
        self.dPort1 = bytes([FormatUtils.intToBytes(data, 2)[1]])
        self.empty = False    
    
    def setFlag(self, data: int):
        self.flag = FormatUtils.intToBytes(data, 1)
        self.empty = False
    
    def setFlagAttr(self, data: int):
        self.flagAttr = FormatUtils.intToBytes(data, 1)
        self.empty = False
    
    def setData(self, data: bytes):
        self.data = FormatUtils.trimBytes(data, 65535)
        self.dlen0 = bytes([FormatUtils.intToBytes(len(self.data), 2)[0]])
        self.dlen1 = bytes([FormatUtils.intToBytes(len(self.data), 2)[1]])
        self.empty = False
    
    def getSource(self) -> str:
        s0 = FormatUtils.bytesToInt(self.src0)
        s1 = FormatUtils.bytesToInt(self.src1)
        s2 = FormatUtils.bytesToInt(self.src2)
        s3 = FormatUtils.bytesToInt(self.src3)
        return FormatUtils.makeOctets([s0, s1, s2, s3])

    def getDest(self) -> str:
        d0 = FormatUtils.bytesToInt(self.dest0)
        d1 = FormatUtils.bytesToInt(self.dest1)
        d2 = FormatUtils.bytesToInt(self.dest2)
        d3 = FormatUtils.bytesToInt(self.dest3)
        return FormatUtils.makeOctets([d0, d1, d2, d3])
    
    def getSourcePort(self) -> int:
        return FormatUtils.bytesToInt(self.sPort0 + self.sPort1)
    
    def getDestPort(self) -> int:
        return FormatUtils.bytesToInt(self.dPort0 + self.dPort1)

    def getAge(self) -> int:
        return FormatUtils.bytesToInt(self.age)

    def getFlag(self) -> int:
        return FormatUtils.bytesToInt(self.flag)

    def getData(self) -> bytes:
        return self.data
    
    def getLength(self) -> int:
        return FormatUtils.bytesToInt(self.dlen0 + self.dlen1)
    
    def incAge(self): # Increment the age of the packet
        age = FormatUtils.bytesToInt(self.age)
        age += 1
        if(age > 255):
            age = 255
        self.age = FormatUtils.intToBytes(age, 1)
        self.empty = False
        
    def save(self) -> bytes: # Save the packet to bytes
        p = self.src0 + self.src1 + self.src2 + self.src3
        p += self.dest0 + self.dest1 + self.dest2 + self.dest3
        p += self.sPort0 + self.sPort1 + self.dPort0 + self.dPort1 
        p += self.flag + self.age + self.dlen0 + self.dlen1
        p += self.data
        return p
    
    def load(self, bdata: bytes): # Load a packet from bytes
        try:
            self.empty = False
            self.src0 = bdata[0:1]
            self.src1 = bdata[1:2]
            self.src2 = bdata[2:3]
            self.src3 = bdata[3:4]
            self.dest0 = bdata[4:5]
            self.dest1 = bdata[5:6]
            self.dest2 = bdata[6:7]
            self.dest3 = bdata[7:8]
            self.sPort0 = bdata[8:9]
            self.sPort1 = bdata[9:10]
            self.dPort0 = bdata[10:11]
            self.dPort1 = bdata[11:12]
            self.flag = bdata[12:13]
            self.age = bdata[13:14]
            self.dlen0 = bdata[14:15]
            self.dlen1 = bdata[15:16]
            dLen = FormatUtils.bytesToInt(self.dlen0 + self.dlen1)
            self.data = bdata[16:16+dLen]
        except Exception as e:
            self.empty = True
            self.src0 = FormatUtils.intToBytes(0, 1)
            self.src1 = FormatUtils.intToBytes(0, 1)
            self.src2 = FormatUtils.intToBytes(0, 1)
            self.src3 = FormatUtils.intToBytes(0, 1)
            self.dest0 = FormatUtils.intToBytes(0, 1)
            self.dest1 = FormatUtils.intToBytes(0, 1)
            self.dest2 = FormatUtils.intToBytes(0, 1)
            self.dest3 = FormatUtils.intToBytes(0, 1)
            self.sPort0 = FormatUtils.intToBytes(0, 1)
            self.sPort1 = FormatUtils.intToBytes(0, 1)
            self.dPort0 = FormatUtils.intToBytes(0, 1)
            self.dPort1 = FormatUtils.intToBytes(0, 1)
            self.flag = FormatUtils.intToBytes(0, 1)
            self.age = FormatUtils.intToBytes(0, 1)
            self.dlen0 = FormatUtils.intToBytes(0, 1)
            self.dlen1 = FormatUtils.intToBytes(0, 1)

################################################################################ High-level operations
class NetworkInterface:
    def __init__(self, address: str, port: int):
        self.address = address
        self.port = port
        self.ri = RadioInterface()
    
    def makePacket(self, data: bytes, dest: str, destPort: int, flag = 0) -> Packet: # Return a Packet with the specified parameters
        return Packet(data, self.address, dest, self.port, destPort, flag)
    
    def sendPacket(self, p: Packet): # Send a Packet
        self.ri.tx(p.save())
    
    def listenForAnyPacket(self, timeout=-1) -> Packet: # Listen for and return any Packet
        while True:
            rd = self.ri.rx(timeout)
            if(rd != b''):
                p = Packet()
                p.load(rd)
                return p
    
    def listenForPacket(self, timeout=-1) -> Packet: # Listen for and return a Packet addressed to this interface
        while True:
            rd = self.ri.rx(timeout)
            if(rd != b''):
                p = Packet()
                p.load(rd)
                if(p.getDest() == self.address and int(p.getDestPort()) == int(self.port)):

                    return p

    def getIntegrity(self) -> float: # Get the integrity of the most recently received Packet
        return self.ri.getIntegrity()