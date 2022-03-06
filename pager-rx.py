from adrcfs import NetworkInterface

print("Mercury Pager Receiver")
print("Homepage: https://radio.jvmeifert.com/mercurypager")
print("Updates: https://github.com/jvmeifert/mercurypager/releases")
print("Enter address to listen on (xxx.xxx.xxx.xxx). BLANK:ANY")
source = input(":")
if(source == ""):
    filterListener = False
    ni = NetworkInterface("255.255.255.255", 65535)
else:
    filterListener = True
    ni = NetworkInterface(source, 65535)

while(True):
    print("Listening for page...\n")
    if(filterListener):
        p = ni.listenForPacket()
    else:
        p = ni.listenForAnyPacket()
    
    # get attributes
    source = p.getSource()
    dest = p.getDest()
    sourcePort = p.getSourcePort()
    destPort = p.getDestPort()
    age = p.getAge()
    flag = p.getFlag()
    length = p.getLength()
    data = p.getData()
    integrity = round(ni.getIntegrity() * 100, 4)

    # display attributes
    print("\nPage received (Integrity: " + str(integrity) + "%)")
    if(integrity < 50):
        print("WARNING: Low page integrity. Uncorrectable errors may be present.")
    print(source + ":" + str(sourcePort) + " -> " + dest + ":" + str(destPort) + " (A: " + str(age) + ", F: " + flag + ", L: " + str(length) + "):")

    # handle contents
    if(p.isGroupFlag()):
        print("Page is a group. Showing grouped pages:")
        gp = p.getGroup()
        # display each packet in group
        for i in gp:
            iSource = i.getSource()
            iDest = i.getDest()
            iSourcePort = i.getSourcePort()
            iDestPort = i.getDestPort()
            iAge = i.getAge()
            iFlag = i.getFlag()
            iLength = i.getLength()
            iData = i.getData()
            print(iSource + ":" + str(iSourcePort) + " -> " + iDest + ":" + str(iDestPort) + " (A: " + str(iAge) + ", F: " + iFlag + ", L: " + str(iLength) + "):")
            print(iData.decode("ascii", "ignore"))
    else:
        # if not a group print the packet's data
        print(data.decode("ascii", "ignore"))
    
    print("Done. (CTRL-C to exit)")