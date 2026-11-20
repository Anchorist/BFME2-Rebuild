import winreg as w
K=r"SOFTWARE\Electronic Arts\Electronic Arts\The Battle for Middle-earth II"
vals={"InstallPath":(w.REG_SZ,'G:\\'),"Language":(w.REG_SZ,"English"),"MapPackVersion":(w.REG_DWORD,0x10000),"UseLocalUserMaps":(w.REG_DWORD,0),"UserDataLeafName":(w.REG_SZ,"My Battle for Middle-earth II Files")}
h=w.CreateKeyEx(w.HKEY_LOCAL_MACHINE,K,0,w.KEY_WRITE|w.KEY_WOW64_32KEY)
for n,(t,v) in vals.items(): w.SetValueEx(h,n,0,t,v)
w.CloseKey(h)
h=w.OpenKeyEx(w.HKEY_LOCAL_MACHINE,K,0,w.KEY_READ|w.KEY_WOW64_32KEY)
print("registry 32-bit view:",repr(w.QueryValueEx(h,"InstallPath")[0]))
