from orion import NetworkInterface

print("Mercury Pager Receiver")
print("Enter address to listen on (xxx.xxx.xxx.xxx). BLANK:ANY")
source = input(":")
if(source == ""):
    filterListener = False
    ni = NetworkInterface("0.0.0.0", 0)
else:
    filterListener = True
    ni = NetworkInterface(source, 65535)

while(True):
    print("Waiting for page...\n")
    if(filterListener):
        p = ni.listenForPacket()
    else:
        p = ni.listenForAnyPacket()
    if(p.isEmpty()):
        print("Corrupt page dropped.")
    else:
        source = p.getSource()
        dest = p.getDest()
        sourcePort = p.getSourcePort()
        destPort = p.getDestPort()
        age = p.getAge()
        flag = p.getFlag()
        length = p.getLength()
        data = p.getData()
        integrity = round(ni.getIntegrity() * 100, 4)
        print("Page received (Integrity: " + str(integrity) + "%)")
        if(integrity < 50):
            print("WARNING: Low page integrity. Uncorrectable errors may be present.")
        print("SRC: " + source + ":" + str(sourcePort) + " DEST: " + dest + ":" + str(destPort) + " FLAG: " + str(flag) + " AGE: " + str(age) + " LEN: " + str(length))
        print("DATA:")
        print(data.decode("ascii", "ignore"))
        print("\nDone. (CTRL-C to exit)")