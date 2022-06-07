"""
Change password on finam server account
"""
import transaq.xconnector as tc
import xml.etree.cElementTree as ET
import time

######################################################
login='zzz'
old_pass='xxx'
new_pass='yyy'
######################################################

connected = False
cmd=f'<command id="change_pass" oldpass="{old_pass}" newpass="{new_pass}" />'

def uc(data):
    global connected
    cmd = tc.GetXmlCmd(data)
    if cmd == tc.XmlConnector.idServerStatus:
        # breakpoint()
        xml = ET.fromstring(data)
        connected = xml.attrib['connected'] == 'true'
        print(data)
        return

conn = tc.XmlConnector()
conn.SetUserCallback(uc)
conn.InitializeEx()
rz = conn.SendCommand(cmd(login, old_pass))
while not connected:
    time.sleep(1)
rz = conn.SendCommand(cmd)
print(rz)