import afskmodem
"""
x------------------------------------x
|      ____  ___  ________  _  __    |
|     / __ \/ _ \/  _/ __ \/ |/ /    |
|    / /_/ / , _// // /_/ /    /     |
|    \____/_/|_/___/\____/_/|_/      |
|                                    |                           
x------------------------------------x
| Open Radio Inter-Operable Network  |
| Protocol v2, Software v1.0         |
| https://github.com/jvmeifert/orion |
x------------------------------------x
"""
################################################################################ General utilities
class FormatUtils:
    def parseOctets(data): # Parse a series of octets given in string form (xxx.xxx.xxx.xxx)
        octs = data.split(".")
        if(len(octs) < 2): # default to 0.0
            octs = ["0","0"]
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
    
    def intToByte(data): # int(0-255) to single byte
        if(data > 255):
            return b'\xff'
        elif(data < 0):
            return b'\x00'
        else:
            return bytes([data])

    def byteToInt(data): # single byte to int(0-255)
        return ord(data)

    def trimBytes(data, val): # shorten bytes object to specified length
        if(len(data) > val):
            return data[0:val]
        else:
            return data

################################################################################ Wrapper class for digital radio interface
class RadioInterface: 
    def __init__(self):
        self.receiver = afskmodem.digitalReceiver(afskmodem.digitalModulationTypes.afsk500()) # ORION v1 runs on top of AFSK500(1000,2000) + Hamming(8,4)
        self.transmitter = afskmodem.digitalTransmitter(afskmodem.digitalModulationTypes.afsk500())
        self.integrity = 1

    def rx(self, timeout=-1): # Listen for and catch a transmission, report bit error rate and return data (bytes)
        rd, te = self.receiver.rx(timeout)
        if(len(rd) > 4): # Only record integrity for transmissions longer than 4 bytes
            self.integrity = 1 - (te / len(rd))
        return rd

    def tx(self, data): # Transmit raw data (bytes)
        self.transmitter.tx(data)

    def getIntegrity(self): # Return integrity of the last received transmission
        return self.integrity

# Packet structure and operations
class Packet:
    def __init__(self, data=b'', source0 = 0, source1 = 0, dest0 = 0, dest1 = 0, flag = 0, flagAttr = 0):
        self.src0 = FormatUtils.intToByte(source0)
        self.src1 = FormatUtils.intToByte(source1)
        self.dest0 = FormatUtils.intToByte(dest0)
        self.dest1 = FormatUtils.intToByte(dest1)
        self.age = FormatUtils.intToByte(0)
        self.flag = FormatUtils.intToByte(flag)
        self.flagAttr = FormatUtils.intToByte(flagAttr)
        self.data = FormatUtils.trimBytes(data, 255)
        self.length = FormatUtils.intToByte(len(self.data))
        self.empty = False
    def isEmpty(self):
        return self.empty
    def setSrc0(self, data):
        self.src0 = FormatUtils.intToByte(data)
        self.empty = False
    
    def setSrc1(self, data):
        self.src1 = FormatUtils.intToByte(data)
        self.empty = False
    
    def setDest0(self, data):
        self.dest0 = FormatUtils.intToByte(data)
        self.empty = False
        
    def setDest1(self, data):
        self.dest1 = FormatUtils.intToByte(data)    
        self.empty = False
    
    def setFlag(self, data):
        self.flag = FormatUtils.intToByte(data)
        self.empty = False
    
    def setFlagAttr(self, data):
        self.flagAttr = FormatUtils.intToByte(data)
        self.empty = False
    
    def setData(self, data):
        self.data = FormatUtils.trimBytes(data, 255)
        self.length = FormatUtils.intToByte(len(self.data))
        self.empty = False
    
    def getSrc0(self):
        return FormatUtils.byteToInt(self.src0)

    def getSrc1(self):
        return FormatUtils.byteToInt(self.src1)

    def getDest0(self):
        return FormatUtils.byteToInt(self.dest0)

    def getDest1(self):
        return FormatUtils.byteToInt(self.dest1)

    def getAge(self):
        return FormatUtils.byteToInt(self.age)

    def getFlag(self):
        return FormatUtils.byteToInt(self.flag)

    def getFlagAttr(self):
        return FormatUtils.byteToInt(self.flagAttr)

    def getData(self):
        return self.data
    
    def getLength(self):
        return FormatUtils.byteToInt(self.length)
    
    def incAge(self): # Increment the age of the packet
        age = FormatUtils.byteToInt(self.age)
        age += 1
        if(age > 255):
            age = 255
        self.age = FormatUtils.intToByte(age)
        self.empty = False
        
    def save(self): # Save the packet to bytes
        return self.src0 + self.src1 + self.dest0 + self.dest1 + self.age + self.flag + self.flagAttr + self.length + self.data
    
    def load(self, bdata): # Load a packet from bytes
        try:
            self.empty = False
            self.src0 = bdata[0:1]
            self.src1 = bdata[1:2]
            self.dest0 = bdata[2:3]
            self.dest1 = bdata[3:4]
            self.age = bdata[4:5]
            self.flag = bdata[5:6]
            self.flagAttr = bdata[6:7]
            self.length = bdata[7:8]
            self.data = bdata[8:8+FormatUtils.byteToInt(self.length)]
        except Exception as e:
            self.empty = True
            self.src0 = FormatUtils.intToByte(0)
            self.src1 = FormatUtils.intToByte(0)
            self.dest0 = FormatUtils.intToByte(0)
            self.dest1 = FormatUtils.intToByte(0)
            self.age = FormatUtils.intToByte(0)
            self.flag = FormatUtils.intToByte(0)
            self.flagAttr = FormatUtils.intToByte(0)
            self.length = FormatUtils.intToByte(0)
            self.data = b''

################################################################################ High-level operations
class NetworkInterface:
    def __init__(self, src0 = 0, src1 = 0):
        self.src0 = src0
        self.src1 = src1
        self.ri = RadioInterface()
    
    def makePacket(self, data, dest0, dest1, flag = 0, flagAttr = 0): # Return a Packet with the specified parameters
        return Packet(data, self.src0, self.src1, dest0, dest1, flag, flagAttr)
    
    def sendPacket(self, p = Packet()): # Send a Packet
        self.ri.tx(p.save())
    
    def listenForPacket(self, timeout=-1): # Listen for and return a Packet
        while True:
            rd = self.ri.rx(timeout)
            if(rd != b''):
                p = Packet()
                p.load(rd)
                return p
    
    def listenForAddressedPacket(self, timeout=-1): # Listen for and return an (addressed) Packet
        while True:
            rd = self.ri.rx(timeout)
            if(rd != b''):
                p = Packet()
                p.load(rd)
                if(p.getDest0() == self.src0 and p.getDest1 == self.src1):
                    return p

    def getIntegrity(self): # Get the integrity of the most recently received Packet
        return self.ri.getIntegrity()
