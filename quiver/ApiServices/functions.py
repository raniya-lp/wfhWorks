import socket   
def FindIpAddress():
    system_address=[]
    hostname=socket.gethostname()   
    IPAddr=socket.gethostbyname(hostname)   
    system_address.append(hostname)
    system_address.append(IPAddr)
    return system_address
