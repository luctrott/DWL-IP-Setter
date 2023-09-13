import serial
import serial.tools.list_ports
import time
import sys
#sys.stdout = open('log.txt', 'w')


def get_ip(start_ip:str="192.168.1.1",end_ip:str="192.168.1.254",subnet_mask:str="255.255.255.0")->list:
    import ipaddress
    binary_subnet = "".join([bin(int(x))[2:].zfill(8) for x in subnet_mask.split(".")])
    cidr = str(len(binary_subnet.rstrip("0")))


    ip=f"{start_ip}/{cidr}"
    network = ipaddress.IPv4Network(ip, strict=False)
    net_id = str(network.network_address)
    x=ipaddress.IPv4Network(f'{net_id}/{cidr}')
    valied=False
    ip_list=[]
    for ip in x:
        if str(ip)==str(start_ip):
            valied=True
        if valied:
            ip_list.append(str(ip))

            if str(ip)==str(end_ip):
                valied=False
    
    return ip_list

def get_com() -> str:
    coms=list(serial.tools.list_ports.comports())

    for num,i in enumerate(coms):
        print(f"[{num}] - {i.name}: {i.description}")
    num=-1
    while True:
        try:
            num=int(input("Geben Sie eine Nummer ein: "))
            if num in range(len(coms)):
                break
        except ValueError:
            pass
    return str(coms[num].name)


class SerialDevice:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.serial=serial.Serial(self.port, self.baudrate,timeout=0.0031)
    
    def wait_for_prompt(self,text):
        prompt = ''
        print(f"waiting for {text}!")
        while not prompt.endswith(text):
            tmp= self.serial.read(1).decode('utf-8')
            prompt += tmp
            if console:
                print(tmp, end='')
        return prompt
    
    def wait_for_prompt2(self,text,text2):
        prompt = ''
        print(f"waiting for {text} or {text2}!")
        while (not prompt.endswith(text)) and (not prompt.endswith(text2)):
            tmp= self.serial.read(1).decode('utf-8')
            prompt += tmp
            if console:
                print(tmp, end='')
            
        return prompt
        
    def send_text(self, text):
            print(f"Sending:{text}!")
            self.serial.write(text.encode('utf-8'))



def login(ser:SerialDevice,user,password):
    x=ser
    time.sleep(1)
    x.wait_for_prompt("Boot Successful - Config Ok")
    time.sleep(1)
    x.send_text("\n")
    time.sleep(1)
    x.wait_for_prompt("DLINK-WLAN-AP login:")
    time.sleep(1)
    x.send_text(f"{user}\n")
    x.wait_for_prompt("Password:")
    time.sleep(1)
    x.send_text(f"{password}\n")
    tmp=x.wait_for_prompt2("DLINK-WLAN-AP#","Login incorrect")
    if "DLINK-WLAN-AP#" in tmp:
        print(f"Successfully Logged in with Username: {user} and Password: {password}")
        return True
    else:
        print(f"Error while Loging in with Username: {user} and Password: {password}")
        return False

def set_ip(ser:SerialDevice,ip):
    x=ser
    x.send_text(f"set management static-ip {ip}\n")
    tmp=x.wait_for_prompt("DLINK-WLAN-AP#")
    if "dman: Restarting DHCP client" in tmp:
        print(f"Successfully set IP to {ip} ")
        return True
    else:
        print(f"Error while setting IP to: {ip} ")
        return False


def set_mask(ser:SerialDevice,mask):
    x=ser
    x.send_text(f"set management static-mask {mask}\n")
    tmp=x.wait_for_prompt("DLINK-WLAN-AP#")
    if "dman: Restarting DHCP client" in tmp:
        print(f"Successfully set mask to {mask} ")
        return True
    else:
        print(f"Error while setting mask to: {mask} ")
        return False

def logout(ser:SerialDevice):
    x=ser
    x.send_text("exit\n")
    x.wait_for_prompt("DLINK-WLAN-AP login:")
    print("Logged out")

def turnoff_dhcp_client(ser:SerialDevice):
    if True:
        x=ser
        x.send_text("set management dhcp-status down\n")
        x.wait_for_prompt("DLINK-WLAN-AP#")
        x.send_text(f"get management dhcp-status\n")
        tmp=x.wait_for_prompt("DLINK-WLAN-AP#")
        if "down" in tmp:
            print(f"Successfully turned off dhcp-client")
            return True
        else:
            print(f"Error while turning off dhcp-client")
            return False
        
def save(ser:SerialDevice):
    x=ser
    x.send_text("save-running\n")
    x.wait_for_prompt("DLINK-WLAN-AP#")
    


def setup(ser,user,password,subnet,ip):
    tmp=False
    x=ser
    if login(x,user,password):
        if set_mask(x,subnet):
            if set_ip(x,ip):
                if turnoff_dhcp_client(x):
                    save(x)
                    tmp=True
        logout(x)
    return tmp

def setup2(ser,user,password,subnet,ip)->bool:
    print(f"Setting IP: {ip}")
    input("Press enter to Start:")
    try:
        return setup(ser,user,password,subnet,ip)
    except:
        return False


if __name__=="__main__":
    
    
    
    com=get_com()
    baud=int(115200)
    x=SerialDevice(com,baud)
    subnet=input("Subnet like 255.255.240.0: ")
    ipstart= input("Start IP like 192.168.0.100: ")
    ipend= input("End IP like 192.168.0.200: ")
    ips=get_ip(ipstart,ipend,subnet)
    user="admin"
    password="admin"
    console= input("Debug (True): ")=="True"
    
    for i in ips:
        while not setup2(x,user,password,subnet,i):
            try:
                num=int(input("Error! Any-Retry 1-Skip 2-Quit: "))
            except KeyboardInterrupt:
                exit()
            except:
                num=0
            if num==0:
                pass
            if num==1:
                break
            elif num==2:
                x.serial.close()
                quit()
    #sys.stdout.close()
    input("Press Enter to exit!")
