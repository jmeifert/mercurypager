from orion import NetworkInterface, FormatUtils

print("Mercury Paging System Receiver")
print("Enter address to listen on ([0-255].[0-255]). 0.0:ANY")
octs = FormatUtils.parseOctets(input(":"))
if(octs == [0,0]):
    filterListener = False
    ni = NetworkInterface()
else:
    filterListener = True
    ni = NetworkInterface(octs[0], octs[1])

while(True):
    try:
        print("Waiting for page...\n")
        if(filterListener):
            p = ni.listenForAddressedPacket()
        else:
            p = ni.listenForPacket()
        if(p.isEmpty()):
            print("Corrupt page dropped.")
        else:
            src0 = p.getSrc0()
            src1 = p.getSrc1()
            dest0 = p.getDest0()
            dest1 = p.getDest1()
            length = p.getLength()
            data = p.getData()
            integrity = round(ni.getIntegrity() * 100, 4)
            print("Page received (Integrity: " + str(integrity) + "%)")
            if(integrity < 50):
                print("WARNING: Low page integrity. Uncorrectable errors may be present.")
            print("SRC: " + str(src0) + "." + str(src1) + ", DEST: " + str(dest0) + "." + str(dest1) + ", LEN: " + str(length) + "\n")
            print(data.decode("ascii", "ignore"))
            print("\nDone. (CTRL-C to exit)")
    except Exception as e:
        print("Exception encountered: " + str(e))
        sleep(1)