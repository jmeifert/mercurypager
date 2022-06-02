import afskmodem
import os
from datetime import datetime
"""
x-------------------------------------------------------------------------x
| ADR-CFS (Asynchronous Digital Radio Communication Formatting Standard ) |
| https://github.com/jmeifert/adr-cfs                                     |
x-------------------------------------------------------------------------x
"""
################################################################################ LOGGING
def get_date_and_time(): # Long date and time for logging
        now = datetime.now()
        return now.strftime('%Y-%m-%d %H:%M:%S')

# Logging level (0: INFO, 1: WARN (recommended), 2: ERROR, 3: NONE)
LOG_LEVEL = 0
#
# Should the log output to the console?
LOG_TO_CONSOLE = True
#
# Should the log output to a log file?
LOG_TO_FILE = False
#
# Where to generate logfile if need be
LOG_PATH = "adr-cfs.log"
#
# How the log identifies which module is logging.
LOG_PREFIX = "(ADR-CFS)"

# Initialize log file if needed
if(LOG_TO_FILE):
    try:
        os.remove(LOG_PATH)
    except:
        pass
    with open(LOG_PATH, "w") as f:
        f.write(get_date_and_time() + " [INFO] " + LOG_PREFIX + " Logging initialized.\n")

def log(level: int, data: str):
    if(level >= LOG_LEVEL):
        output = get_date_and_time()
        if(level == 0):
            output += " [INFO] "
        elif(level == 1):
            output += " [WARN] "
        else:
            output += " [ERR!] "
        output += LOG_PREFIX + " "
        output += data
        if(LOG_TO_FILE):
            with open(LOG_PATH, "a") as f:
                f.write(output + "\n")
        if(LOG_TO_CONSOLE):
            print(output)

################################################################################ General utilities
class FormatUtils:
    # Parse a series of octets given in string form and of a given length (xxx.xxx.xxx.xxx)
    def parse_address(data: str) -> list: 
        octs = data.split(".")
        p = []
        for i in octs:
            p.append(int(i))
        return p
    
    # Convert a list of ints into nicely formatted string octets (xxx.xxx.xxx.xxx)
    def make_address(data: list) -> str:
        p = ""
        for i in data:
            mi = i
            p += str(mi) + "."
        return p.rstrip(".")
    
    # Parse a socket (xxx.xxx.xxx.xxx:0-65535) address and return its values ["xxx.xxx.xxx.xxx", port]
    def parse_socket_address(data: str) -> list:
        p = data.split(":")
        a = str(p[0])
        b = int(p[1])
        return a, b
    
    # Make a socket (xxx.xxx.xxx.xxx:0-65535) address from its values [oct0, oct1, oct2, oct3, port]
    def make_socket_address(data: list) -> str:
        o = ""
        for i in range(5):
            if(i == 4):
                o += ":" + str(data[i])
            elif(i == 3):
                o += str(data[i])
            else:
                o += str(data[i]) + "."
        return o
    
    # Check if an address is valid
    def is_valid_address(data: str):
        octs = data.split(".")
        if(len(octs) == 4):
            try:
                for i in octs:
                    if(int(i) > 255 or int(i) < 0):
                        return False
                return True
            except:
                return False
        return False
    
    # Check if a socket address is valid
    def is_valid_socket_address(data: str):
        if(":" in data):
            a = data.split(":")
            if(FormatUtils.is_valid_address(a[0])):
                try:
                    p = int(a[1])
                    if(p < 65536 and p > 0):
                        return True
                except:
                    return False
        return False
    
    # int to n bytes
    def int_to_bytes(data: int, n: int) -> bytes: 
        if(data > (256 ** n) - 1):
            data = (256 ** n) - 1
        if(data < 0):
            data = 0
        return data.to_bytes(n, "big") # network endianness

    # bytes to int
    def bytes_to_int(data: bytes) -> int: 
        return int.from_bytes(data , "big")

    # shorten bytes object to specified length
    def trim_bytes(data, val: bytes) -> bytes: 
        if(len(data) > val):
            return data[0:val]
        else:
            return data

    # convert bits to an integer from 0-255
    def bits_to_int(bData: str) -> int:
        return int(bData[0:8], 2)
    
    # convert an integer from 0-255 to bits
    def int_to_bits(bData: int) -> str:
        return '{0:08b}'.format(bData)
    
################################################################################ Wrapper class for digital radio interface
class RadioInterface: 
    def __init__(self):
        self.receiver = afskmodem.DigitalReceiver(afskmodem.DigitalModulationTypes.afsk1200()) # see AFSKmodem README.md for more info on these
        self.transmitter = afskmodem.DigitalTransmitter(afskmodem.DigitalModulationTypes.afsk1200())
        self.integrity = 1

    def rx(self, timeout=-1): # Listen for and catch a transmission, report bit error rate and return data (bytes)
        rd, te = self.receiver.rx(timeout)
        if(len(rd) > 12): # Only record integrity for transmissions longer than 12 bytes (header is 16 bytes)
            self.integrity = 1 - (te / len(rd))
        return rd

    def tx(self, data: bytes): # Transmit raw data (bytes)
        self.transmitter.tx(data)

    def get_integrity(self) -> float: # Return integrity of the last received transmission
        return self.integrity

################################################################################ Packet structure and operations
class Packet:
    def __init__(self, data=b'', source = "0.0.0.0", dest = "0.0.0.0", sPort = 0, dPort = 0):
        self.source = FormatUtils.parse_address(source)
        self.dest = FormatUtils.parse_address(dest)
        # Source address
        self.src0 = FormatUtils.int_to_bytes(self.source[0], 1)
        self.src1 = FormatUtils.int_to_bytes(self.source[1], 1)
        self.src2 = FormatUtils.int_to_bytes(self.source[2], 1)
        self.src3 = FormatUtils.int_to_bytes(self.source[3], 1)
        # Dest address
        self.dest0 = FormatUtils.int_to_bytes(self.dest[0], 1)
        self.dest1 = FormatUtils.int_to_bytes(self.dest[1], 1)
        self.dest2 = FormatUtils.int_to_bytes(self.dest[2], 1)
        self.dest3 = FormatUtils.int_to_bytes(self.dest[3], 1)
        # Source port
        self.sPort0 = bytes([FormatUtils.int_to_bytes(sPort, 2)[0]])
        self.sPort1 = bytes([FormatUtils.int_to_bytes(sPort, 2)[1]])
        # Dest port
        self.dPort0 = bytes([FormatUtils.int_to_bytes(dPort, 2)[0]])
        self.dPort1 = bytes([FormatUtils.int_to_bytes(dPort, 2)[1]])
        # Data
        self.data = FormatUtils.trim_bytes(data, 1024)
        # Params
        self.flag = FormatUtils.int_to_bytes(0, 1)
        self.age = FormatUtils.int_to_bytes(0, 1)
        self.dlen0 = bytes([FormatUtils.int_to_bytes(len(self.data), 2)[0]])
        self.dlen1 = bytes([FormatUtils.int_to_bytes(len(self.data), 2)[1]])
        self.empty = False
    
    # Return TRUE if this Packet is empty.
    def is_empty(self) -> bool:
        return self.empty

    # Set the source address of this Packet
    def set_source(self, data: str):
        self.source = FormatUtils.parse_address(data)
        self.src0 = FormatUtils.int_to_bytes(self.source[0], 1)
        self.src1 = FormatUtils.int_to_bytes(self.source[1], 1)
        self.src2 = FormatUtils.int_to_bytes(self.source[2], 1)
        self.src3 = FormatUtils.int_to_bytes(self.source[3], 1)
        self.empty = False
    
    # Set the destination address of this Packet
    def set_dest(self, data: str):
        self.dest = FormatUtils.parse_address(data)
        self.dest0 = FormatUtils.int_to_bytes(self.dest[0], 1)
        self.dest1 = FormatUtils.int_to_bytes(self.dest[1], 1)
        self.dest2 = FormatUtils.int_to_bytes(self.dest[2], 1)
        self.dest3 = FormatUtils.int_to_bytes(self.dest[3], 1)
        self.empty = False

    # Set the source port of this Packet
    def set_source_port(self, data: int):
        self.sPort0 = bytes([FormatUtils.int_to_bytes(data, 2)[0]])
        self.sPort1 = bytes([FormatUtils.int_to_bytes(data, 2)[1]])
        self.empty = False

    # Set the destination port of this Packet
    def set_dest_port(self, data: int):
        self.dPort0 = bytes([FormatUtils.int_to_bytes(data, 2)[0]])
        self.dPort1 = bytes([FormatUtils.int_to_bytes(data, 2)[1]])
        self.empty = False    
    
    # Set the flag byte of this Packet
    def set_flag(self, data: str):
        iv = FormatUtils.bits_to_int(data)
        self.flag = FormatUtils.int_to_bytes(iv, 1)
        self.empty = False
    
    # Set the data payload of this Packet
    def set_data(self, data: bytes):
        self.data = FormatUtils.trim_bytes(data, 1024)
        self.dlen0 = bytes([FormatUtils.int_to_bytes(len(self.data), 2)[0]])
        self.dlen1 = bytes([FormatUtils.int_to_bytes(len(self.data), 2)[1]])
        self.empty = False
    
    # Get the source address of this Packet
    def get_source(self) -> str:
        s0 = FormatUtils.bytes_to_int(self.src0)
        s1 = FormatUtils.bytes_to_int(self.src1)
        s2 = FormatUtils.bytes_to_int(self.src2)
        s3 = FormatUtils.bytes_to_int(self.src3)
        return FormatUtils.make_address([s0, s1, s2, s3])

    # Get the destination address of this Packet
    def get_dest(self) -> str:
        d0 = FormatUtils.bytes_to_int(self.dest0)
        d1 = FormatUtils.bytes_to_int(self.dest1)
        d2 = FormatUtils.bytes_to_int(self.dest2)
        d3 = FormatUtils.bytes_to_int(self.dest3)
        return FormatUtils.make_address([d0, d1, d2, d3])
    
    # Get the source port of this Packet
    def get_source_port(self) -> int:
        return FormatUtils.bytes_to_int(self.sPort0 + self.sPort1)
    
    # Get the destination port of this Packet
    def get_dest_port(self) -> int:
        return FormatUtils.bytes_to_int(self.dPort0 + self.dPort1)

    # Get the age of this Packet
    def get_age(self) -> int:
        return FormatUtils.bytes_to_int(self.age)

    # Get the flag byte of this Packet
    def get_flag(self) -> str:
        iv = FormatUtils.bytes_to_int(self.flag)
        return FormatUtils.int_to_bits(iv)

    # Get the data payload of this Packet
    def get_data(self) -> bytes:
        return self.data
    
    # Get the data length of this Packet
    def get_length(self) -> int:
        return FormatUtils.bytes_to_int(self.dlen0 + self.dlen1)
    
    # Increment the age of this Packet
    def increment_age(self): 
        age = FormatUtils.bytes_to_int(self.age)
        age += 1
        if(age > 255):
            age = 255
        self.age = FormatUtils.int_to_bytes(age, 1)
        self.empty = False

    # Get the GROUP flag on this Packet
    def is_group_flag(self) -> bool:
        sf = self.get_flag()
        if(sf[0] == "1"):
            return True
        return False
    
    # Set the GROUP flag on this Packet
    def set_group_flag(self, v: bool):
        f = self.get_flag()
        sf = list(f)
        if(v):
            sf[0] = "1"
        else:
            sf[0] = "0"
        jf = "".join(sf)
        self.set_flag(jf)
    
    # Get the CHECKSUM flag on this Packet
    def is_checksum_flag(self) -> bool:
        sf = self.get_flag()
        if(sf[1] == "1"):
            return True
        return False
    
    # Set the CHECKSUM flag on this Packet
    def set_checksum_flag(self, v: bool):
        f = self.get_flag()
        sf = list(f)
        if(v):
            sf[1] = "1"
        else:
            sf[1] = "0"
        jf = "".join(sf)
        self.set_flag(jf)
    
    # Get the SIGNATURE flag on this Packet
    def is_signature_flag(self) -> bool:
        sf = self.get_flag()
        if(sf[2] == "1"):
            return True
        return False
    
    # Set the SIGNATURE flag on this Packet
    def set_signature_flag(self, v: bool):
        f = self.get_flag()
        sf = list(f)
        if(v):
            sf[2] = "1"
        else:
            sf[2] = "0"
        jf = "".join(sf)
        self.set_flag(jf)
    
    # Get the KEY flag on this Packet
    def is_key_flag(self) -> bool:
        sf = self.get_flag()
        if(sf[3] == "1"):
            return True
        return False
    
    # Set the KEY flag on this Packet
    def set_key_flag(self, v: bool):
        f = self.get_flag()
        sf = list(f)
        if(v):
            sf[3] = "1"
        else:
            sf[3] = "0"
        jf = "".join(sf)
        self.set_flag(jf)

    # Get the ENCODING flag on this Packet
    def is_encoding_flag(self) -> bool:
        sf = self.get_flag()
        if(sf[4] == "1"):
            return True
        return False
    
    # Set the ENCODING flag on this Packet
    def set_encoding_flag(self, v: bool):
        f = self.get_flag()
        sf = list(f)
        if(v):
            sf[4] = "1"
        else:
            sf[4] = "0"
        jf = "".join(sf)
        self.set_flag(jf)
    
    # Get the FORMATTING flag on this Packet
    def is_formatting_flag(self) -> bool:
        sf = self.get_flag()
        if(sf[5] == "1"):
            return True
        return False
    
    # Set the FORMATTING flag on this Packet
    def set_formatting_flag(self, v: bool):
        f = self.get_flag()
        sf = list(f)
        if(v):
            sf[5] = "1"
        else:
            sf[5] = "0"
        jf = "".join(sf)
        self.set_flag(jf)
    
    # Get the ENCRYPTION flag on this Packet
    def is_encryption_flag(self) -> bool:
        sf = self.get_flag()
        if(sf[6] == "1"):
            return True
        return False
    
    # Set the ENCRYPTION flag on this Packet
    def set_encryption_flag(self, v: bool):
        f = self.get_flag()
        sf = list(f)
        if(v):
            sf[6] = "1"
        else:
            sf[6] = "0"
        jf = "".join(sf)
        self.set_flag(jf)

    # Get the SUBHEADER flag on this Packet
    def is_subheader_flag(self) -> bool:
        sf = self.get_flag()
        if(sf[7] == "1"):
            return True
        return False
    
    # Set the SUBHEADER flag on this Packet
    def set_subheader_flag(self, v: bool):
        f = self.get_flag()
        sf = list(f)
        if(v):
            sf[7] = "1"
        else:
            sf[7] = "0"
        jf = "".join(sf)
        self.set_flag(jf)

    # Save the packet to bytes
    def save(self) -> bytes: 
        p = self.src0 + self.src1 + self.src2 + self.src3
        p += self.dest0 + self.dest1 + self.dest2 + self.dest3
        p += self.sPort0 + self.sPort1 + self.dPort0 + self.dPort1 
        p += self.flag + self.age + self.dlen0 + self.dlen1
        p += self.data
        return p
    
    # Load a packet from bytes
    def load(self, bdata: bytes): 
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
            dLen = FormatUtils.bytes_to_int(self.dlen0 + self.dlen1)
            self.data = bdata[16:16+dLen]
        except Exception as e:
            self.empty = True
            self.src0 = FormatUtils.int_to_bytes(0, 1)
            self.src1 = FormatUtils.int_to_bytes(0, 1)
            self.src2 = FormatUtils.int_to_bytes(0, 1)
            self.src3 = FormatUtils.int_to_bytes(0, 1)
            self.dest0 = FormatUtils.int_to_bytes(0, 1)
            self.dest1 = FormatUtils.int_to_bytes(0, 1)
            self.dest2 = FormatUtils.int_to_bytes(0, 1)
            self.dest3 = FormatUtils.int_to_bytes(0, 1)
            self.sPort0 = FormatUtils.int_to_bytes(0, 1)
            self.sPort1 = FormatUtils.int_to_bytes(0, 1)
            self.dPort0 = FormatUtils.int_to_bytes(0, 1)
            self.dPort1 = FormatUtils.int_to_bytes(0, 1)
            self.flag = FormatUtils.int_to_bytes(0, 1)
            self.age = FormatUtils.int_to_bytes(0, 1)
            self.dlen0 = FormatUtils.int_to_bytes(0, 1)
            self.dlen1 = FormatUtils.int_to_bytes(0, 1)
    
    # Write bytes to build a Packet
    def __write_raw(self, src0, src1, src2, src3, 
                    dest0, dest1, dest2, dest3,
                    sPort0, sPort1, dPort0, dPort1,
                    flag, age, dlen0, dlen1, data):
        self.src0 = src0
        self.src1 = src1
        self.src2 = src2
        self.src3 = src3
        self.dest0 = dest0
        self.dest1 = dest1
        self.dest2 = dest2
        self.dest3 = dest3
        self.sPort0 = sPort0
        self.sPort1 = sPort1
        self.dPort0 = dPort0
        self.dPort1 = dPort1
        self.flag = flag
        self.age = age
        self.dlen0 = dlen0
        self.dlen1 = dlen1
        self.data = data
    
    # Extract grouped packets from their container
    def get_grouped_packets(self):
        try:
            if(not self.is_group_flag()):
                return []
            op = []
            n = 0
            pd = self.get_data()
            while(n < len(pd) - 16):
                log(0, "Reading grouped packet at index " + str(n))
                gp = Packet() # instantiate a packet and read into it
                src0 = pd[n:n+1]
                src1 = pd[n+1:n+2]
                src2 = pd[n+2:n+3]
                src3 = pd[n+3:n+4]
                dest0 = pd[n+4:n+5]
                dest1 = pd[n+5:n+6]
                dest2 = pd[n+6:n+7]
                dest3 = pd[n+7:n+8]
                sPort0 = pd[n+8:n+9]
                sPort1 = pd[n+9:n+10]
                dPort0 = pd[n+10:n+11]
                dPort1 = pd[n+11:n+12]
                flag = pd[n+12:n+13]
                age = pd[n+13:n+14]
                dlen0 = pd[n+14:n+15]
                dlen1 = pd[n+15:n+16]
                dLen = FormatUtils.bytes_to_int(dlen0 + dlen1)
                if(n+16+dLen > len(pd)): # do not overflow
                    break
                data = pd[n+16:n+16+dLen]
                gp.__write_raw(src0, src1, src2, src3, # write to packet
                                dest0, dest1, dest2, dest3,
                                sPort0, sPort1, dPort0, dPort1,
                                flag, age, dlen0, dlen1, data)
                op.append(gp) # store packet in array
                n = n + 16 + dLen # next packet
            return(op)
        except:
            log(1, "Failed to extract grouped packets.")
            return []

################################################################################ High-level operations
class NetworkInterface:
    def __init__(self, address: str, port: int):
        self.address = address
        self.port = port
        self.ri = RadioInterface()
        log(0, "Instantiated a NetworkInterface on socket address " + self.address + ":" + str(self.port) + ".")
    
    # Return a Packet with the specified parameters
    def make_packet(self, data: bytes, dest: str, destPort: int) -> Packet:
        return Packet(data, self.address, dest, self.port, destPort)
    
    # Send a Packet
    def send_packet(self, p: Packet):
        log(0, "Sending a Packet addressed to " + p.get_dest() + ":" + str(p.get_dest_port()) + ".")
        self.ri.tx(p.save())
    
    # Listen for and return any Packet
    def listen_for_any_packet(self, timeout=-1) -> Packet: 
        log(0, "Listening for any Packet...")
        while True:
            rd = self.ri.rx(timeout)
            if(rd != b''):
                p = Packet()
                p.load(rd)
                log(0, "Caught a Packet addressed to " + p.get_dest() + ":" + str(p.get_dest_port()) + ".")
                return p
    
    # Listen for and return a Packet addressed to this interface
    def listen_for_packet(self, timeout=-1) -> Packet: 
        log(0, "Listening for a Packet addressed to this NetworkInterface (" + self.address + ":" + str(self.port) + ")...")
        while True:
            rd = self.ri.rx(timeout)
            if(rd != b''):
                p = Packet()
                p.load(rd)
                if(p.get_dest() == self.address and int(p.get_dest_port()) == int(self.port)):
                    log(0, "Received a Packet addressed to this NetworkInterface (" + self.address + ":" + str(self.port) + ").")
                    return p
    
    # Get the integrity of the most recently received Packet
    def get_integrity(self) -> float: 
        return self.ri.get_integrity()
