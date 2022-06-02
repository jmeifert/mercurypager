from adrcfs import NetworkInterface

print("----- Mercury Pager Receiver -----")
print("- Homepage: https://github.com/jmeifert/mercurypager")
print("- Updates: https://github.com/jmeifert/mercurypager/releases")
print("Enter address to listen on (xxx.xxx.xxx.xxx). BLANK:ANY")
this_addr = input(":")
if(this_addr == ""):
    filterListener = False
    ni = NetworkInterface("255.255.255.255", 65535)
else:
    filterListener = True
    ni = NetworkInterface(this_addr, 65535)

while(True):
    print("Listening for pages...\n")
    if(filterListener):
        p = ni.listen_for_packet()
    else:
        p = ni.listen_for_any_packet()
    
    # get attributes
    p_source = p.get_source()
    p_dest = p.get_dest()
    p_source_port = p.get_source_port()
    p_dest_port = p.get_dest_port()
    p_age = p.get_age()
    p_flag = p.get_flag()
    p_length = p.get_length()
    p_data = p.get_data()
    p_integrity = round(ni.get_integrity() * 100, 4)

    # display attributes
    print("\nPage received (Integrity: " + str(p_integrity) + "%)")
    if(p_integrity < 70):
        print("WARNING: Low page integrity. Uncorrectable errors may be present.")
    print(str(p_source) + ":" + str(p_source_port) + " -> " + str(p_dest) + ":" + str(p_dest_port)
     + " (A: " + str(p_age) + ", F: " + p_flag + ", L: " + str(p_length) + "):")

    # handle contents
    if(p.is_group_flag()):
        print("Page is a group. Showing grouped pages:")
        gp = p.get_grouped_packets()
        # display each packet in group
        for i in gp:
            i_source = i.get_source()
            i_dest = i.get_dest()
            i_source_port = i.get_source_port()
            i_dest_port = i.get_dest_port()
            i_age = i.get_age()
            i_flag = i.get_flag()
            i_length = i.get_length()
            i_data = i.get_data()
            print(i_source + ":" + str(i_source_port) + " -> " + i_dest + ":" + str(i_dest_port) + " (A: " + str(i_age) + ", F: " + i_flag + ", L: " + str(i_length) + "):")
            print(i_data.decode("ascii", "ignore"))
    else:
        # if not a group print the packet's data
        print(p_data.decode("ascii", "ignore"))
    
    print("Done. (CTRL-C to exit)")