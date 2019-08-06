from tkinter import *
from tkinter import messagebox
import RPi.GPIO as gpio
import pigpio
from os import system
from urllib.request import urlopen

from db_lib import *
import Decoder as NECD
from IR_Decode import *
from calculate_frequency import *

KEY_0 = 0;
KEY_1 = 1;
KEY_2 = 2;
KEY_3 = 3;
KEY_4 = 4;
KEY_5 = 5;
KEY_6 = 6;
KEY_7 = 7;
KEY_8 = 8;
KEY_9 = 9;
KEY_VOL_UP = 10;
KEY_VOL_DOWN = 11;
KEY_VOL_MUTE = 12;
KEY_CH_UP = 13;
KEY_CH_DOWN = 14;
KEY_POWER = 15;
KEY_SELECT = 16;
KEY_BACK = 17;
KEY_EXIT = 18;
KEY_MENU = 19;
KEY_INFO = 20;
KEY_UP_BUTTON = 21;
KEY_DOWN_BUTTON = 22;
KEY_LEFT_BUTTON = 23;
KEY_RIGHT_BUTTON = 24;
KEY_OK = 25;
KEY_RED = 26;
KEY_GREEN = 27;
KEY_YELLOW = 28;
KEY_BLUE = 29;
KEY_PLAY = 30;
KEY_REWIND = 31;
KEY_FAST_FORWARD = 32;
KEY_RECORD = 33;
KEY_PAUSE = 34;
KEY_STOP = 35;
KEY_SOURCE = 36;
KEY_OPTIONS = 37;
KEY_LANGUAGE = 38;
KEY_GUIDE = 39;
KEY_PREVIOUS = 40;
KEY_NEXT = 41;

key_names = ["KEY_0", "KEY_1", "KEY_2", "KEY_3", "KEY_4", "KEY_5", "KEY_6", "KEY_7", "KEY_8", "KEY_9", "KEY_VOL_UP ", "KEY_VOL_DOWN ", "KEY_VOL_MUTE ", "KEY_CH_UP ", "KEY_CH_DOWN ", "KEY_POWER ", "KEY_SELECT ", "KEY_BACK ", "KEY_EXIT ", "KEY_MENU ", "KEY_INFO ", "KEY_UP_BUTTON ", "KEY_DOWN_BUTTON ", "KEY_LEFT_BUTTON ", "KEY_RIGHT_BUTTON ", "KEY_OK ", "KEY_RED ", "KEY_GREEN ", "KEY_YELLOW ", "KEY_BLUE ", "KEY_PLAY ", "KEY_REWIND ", "KEY_FAST_FORWARD ", "KEY_RECORD ", "KEY_PAUSE ", "KEY_STOP ", "KEY_SOURCE ", "KEY_OPTIONS ", "KEY_LANGUAGE ", "KEY_GUIDE ", "KEY_PREVIOUS ", "KEY_NEXT "]

previous_key = None
previous_result = None
remote_state = None
remote_id = None
online_remote_id = None
orid = list()
o_remote_id = None
remote_name = None
toggle_present = None
toggle_mask = None
check = list()
o_remote_names = list()
mn = 0
LB = None
auto_update_ready = False
protocol_id = None
check = [0,0,0]
in_toggle = None
frequency = None

top = Tk()
top.config(bg = "grey")
top.title("REMOTE")
top.geometry("940x670")

def get_new_remote_name():
    global e
    string = e.get()
    remote_name = string
    return remote_name

def get_key_id():
    global f
    string = f.get()
    key_id = string
    print(key_id)
    return key_id

L1 = Label(top,text = "Remote Name",bg = 'grey')
L1.place(x=301,y=170)
e = Entry(top,width = 42)
e.pack()
e.place(x =301,y = 190)
e.focus_set()

L2 = Label(top,text = "Enter the key ID",bg = 'grey')
L2.place(x=301,y=435)
f = Entry(top,width = 42)
f.pack()
f.place(x =301,y = 455)
f.focus_set()

L3 = Label(top,text = "AUTO UPDATE",bg = 'grey')
L3.place(x=615,y=7)

var = StringVar()
status = StringVar()
remote_status = StringVar()
remote_details = StringVar()
toggle_status = StringVar()
edit_status = StringVar()

r = "_________________RESULT_________________\n"
result_box = Message(top,textvariable = var,relief = GROOVE,width = 260,pady = 5)
result_box.config(justify = 'left',anchor = 'n',width = 295)
result_box.pack()
result_box.place(x=301,y=98)
var.set(r+"\n\n")

s = "_________________STATUS_________________\n"
status_box = Message(top,textvariable = status,relief = GROOVE,width = 295,justify = 'left',anchor = 'n')
status_box.pack()
status_box.place(x=301,y=10)
status.set(s+"\n\n\n")

rs = "REMOTE STATUS : \n"
remote_status_box = Message(top,textvariable = remote_status,relief = GROOVE,width = 150,justify = 'left',anchor = 'n')
remote_status_box.pack()
remote_status_box.place(x=301,y=222)
remote_status.set(rs)

rd = "REMOTE DETAILS :\n"
remote_details_box = Message(top,textvariable = remote_details,relief = GROOVE,width = 150,justify = 'left',anchor = 'n')
remote_details_box.pack()
remote_details_box.place(x=301,y=262)
remote_details.set(rd+"\n")

ts = " _____________TOGGLE STATUS_____________ \n"
toggle_status_box = Message(top,textvariable = toggle_status,relief = GROOVE,width = 295,justify = 'left',pady = 5,anchor = 'n')
toggle_status_box.pack()
toggle_status_box.place(x=301,y=315)
toggle_status.set(ts+"\n\n")

es = "_______________EDIT STATUS_______________ \n"
edit_status_box = Message(top,textvariable = edit_status,relief = GROOVE,width = 295,justify = 'left',pady = 5,anchor = 'n')
edit_status_box.pack()
edit_status_box.place(x=301,y=480)
edit_status.set(es+"\n")

auto_update_status = StringVar()
keys_display = StringVar()

au = " ___________AUTO UPDATE STATUS___________ \n"
auto_update_status_box = Message(top,textvariable = auto_update_status,relief = GROOVE,width = 320,justify = 'left',pady = 5,anchor = 'n')
auto_update_status_box.pack()
auto_update_status_box.place(x=615,y=25)
auto_update_status.set(au+"\n\n")

kd = " _______________KEYS FOUND_______________ \n"
keys_display_box = Message(top,textvariable = keys_display,relief = GROOVE,width = 295,justify = 'left',pady = 5,anchor = 'n')
keys_display_box.pack()
keys_display_box.place(x=615,y=105)
keys_display.set(kd+"\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")

system("sudo pigpiod")

def count(num):
    print(num)
    print(hex(num))
    binary = bin(num)[2:]
    print(len(binary))
    return len(binary)


def online_check(result,key_code):
    online_result = None
    global remote_id
    global online_remote_id
    global check
    global protocol_id
    global orid
    global o_remote_names
    m = str(hex(result))
    if protocol_id==0:
        l = count(result)
        if l%4 != 0:
            for i in range(4):
                if (l+i)%4==0:
                    l = l+i
                    break
        if(l!=32 and (32-l)==4):
            m = str(hex(result))
            print(m)
            m = m[:2]+"0"+m[2:]
            print(m)
            a = int(m,16)
            print(a)

    
    global mn
    url = "http://sensalore.com/api/v1/remote_prefix?prefix="+m
    print(url)
    response = urlopen(url)
    html = response.read()
    y=0
    x=0
    orid = list()
    o_remote_names = list()
    s = "the remotes with this code are : \n"
    while(1):
        m = str(html)
        x = m.find("&quot;id&quot;: ",y)
        if x==-1:
            break
        y = m.find(",",x)
        h = x + len("&quot;id&quot;: ")
        data = m[h:y]

        m = str(html)
        x = m.find("&quot;name&quot;: &quot;",y)
        if x==-1:
            break
        y = m.find("&quot;,",x)
        h = x + len("&quot;name&quot;: &quot;")
        name = m[h:y]

        print(data,"    ",name)
        s = s+str(data)+"    "+str(name)+"\n"
        online_remote_id = int(data,10)
        online_result = online_remote_check(online_remote_id,key_code)
        print(online_result)
        if online_result == None:
            continue
        print("the code in the db is "+str(hex(online_result)))
        if(mn==3):
            return
        if(result == online_result):
            check[mn]=1
            mn +=1
            print("MATCH NO : "+str(mn))
            orid.append(online_remote_id)
            o_remote_names.append(name)
            keys_display.set(kd+s+"\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
            auto_update_status.set(au+"The code for "+key_names[key_code]+" is "+str(hex(result))+"\n"+"it is a match for the code for "+key_names[key_code]+" in an existing remote.\n"+"the code is "+str(hex(online_result)))
        else:
            print("NO MATCH")
            keys_display.set(kd+s+"\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
            auto_update_status.set(au+"The code for "+key_names[key_code]+" does not match a code in an existing remote.\n")
            #return 0

def assign(key_code):
    global previous_result
    global previous_key
    global remote_id
    global toggle_mask
    global online_remote_id
    global check
    global mn
    global remote_state
    global auto_update_ready
    global protocol_id
    global frequency
    global key_names
    global o_remote_names
    global orid
    if(remote_id == None):
        status.set(s+"SELECT A REMOTE...\n\n")
        return
    status.set(s+"PRESS THE KEY....\n"+"...DECODING...\n")
    if(frequency == None or frequency == 0):
        status.set(s+"CALCULATE THE FREQUENCY...\n\n\n")
        return
    print(frequency)
    result = code(frequency)
    previous_result = result
    previous_key = key_code
    protocol_id = p()
    print("protocol_id = ",protocol_id)
    print("remote ID - ",remote_id)
    create_insert(remote_id,protocol_id,key_code,result)
    var.set(r+"The code for "+key_names[key_code]+" is "+str(hex(result))+"\n\n")
    print("result is "+str(hex(result)))
    status.set(s+"DECODE DONE\n\n\n")    
    if(toggle_mask==None and remote_state!=0 and in_toggle==None):
        toggle_()

    a = online_check(result,key_code)
    if protocol_id == 3:
        print("checking the toggled result")
        toggled = result ^ 32768
        print(hex(toggled))
        online_check(toggled,key_code)
    print(orid)
    for i in range(3):
        print("check[",i,"] = ",check[i])
    print(mn)
    keys = list()
    codes = list()
    msg = "This is the remote found\n"+"KEYS        KEY_NAME      CODES               \n"

    if(check[0]==1 and check[1]==1 and check[2]==1):
        print("_________REMOTE FOUND_________")
        print(orid)
        print(o_remote_names)
        status.set(s+"A remote with the codes is found\n"+"The data for this remote can be automatically completed")
        for i in range(0,len(orid)):
            num_keys = count_return(orid[i])
            keys = key_map(orid[i])
            codes = code_map(orid[i])
            msg = msg + "The remote ID is "+str(orid[i])+"\n"+"The remote is "+str(o_remote_names[i])+"\n"
            for i in range(num_keys):
                msg = msg + str(keys[i])+"     "+ str(key_names[keys[i]])+"    "+str(codes[i])+"\n"
        auto_update_ready = True
        mn = 0
        print("_____________________AUTO UPDATE READY_____________________")
    else:
        print("no remote")
        #auto_update_status.set(au+"No remote found")

    if(len(keys)!=0):
        keys_display.set(kd+msg)

    return

def toggle_():
    global previous_result
    global previous_key
    global toggle_present
    global toggle_mask
    global remote_id
    global protocol_id
    global in_toggle
    global remote_name
    in_toggle = 1
    print("checking for toggle.....")
    length = count(previous_result)      
    if length%4 != 0:
        for i in range(4):
            if (length+i)%4==0:
                length = length+i
                break

    print(length)
    if(protocol_id==1 or protocol_id==2 or protocol_id==3 or protocol_id==4 or protocol_id==5 or protocol_id==10):
        toggle_status.set(ts+"This protocol might have a toggle_mask.\n"+"Press the same key to find the toggle")
        first = previous_result
        status.set(s+"PRESS THE SAME KEY\n"+"PRESS THE SAME KEY\n"+"PRESS THE SAME KEY\n")
        assign(previous_key)
        second = previous_result
        toggle_mask = first ^ second
        print("Toggle mask = "+str(hex(toggle_mask)))
        toggle_status.set(ts+"There is a toggle present for this protocol.\n"+"Toggle mask = "+str(hex(toggle_mask)))
        toggle_present = 1
        remote_db(remote_id,remote_name,protocol_id,length,toggle_present,toggle_mask)
        return
    else:
        print("No toggle")
        toggle_status.set(ts+"There is no toggle for this protocol.\n")
        toggle_present = 0
        toggle_mask = 0
        remote_db(remote_id,remote_name,protocol_id,length,toggle_present,toggle_mask)
        return

def power_click():
    assign(KEY_POWER)

def info_click():
    assign(KEY_INFO)
                                                  
def mute_click():
    assign(KEY_VOL_MUTE)

def one_click():
    assign(KEY_1)

def two_click():
    assign(KEY_2)

def three_click():
    assign(KEY_3)

def four_click():
    assign(KEY_4)

def five_click():
    assign(KEY_5)

def six_click():
    assign(KEY_6)

def seven_click():
    assign(KEY_7)

def eight_click():
    assign(KEY_8)

def nine_click():
    assign(KEY_9)

def zero_click():
    assign(KEY_0)

def vol_up_click():
    assign(KEY_VOL_UP)

def vol_down_click():
    assign(KEY_VOL_DOWN)

def ch_up_click():
    assign(KEY_CH_UP)

def ch_down_click():
    assign(KEY_CH_DOWN)

def back_click():
    assign(KEY_BACK)

def exit_click():
    assign(KEY_EXIT)

def menu_click():
    assign(KEY_MENU)

def source_click():
    assign(KEY_SOURCE)

def options_click():
    assign(KEY_OPTIONS)

def previous_click():
    assign(KEY_PREVIOUS)

def next_click():
    assign(KEY_NEXT)

def language_click():
    assign(KEY_LANGUAGE)

def guide_click():
    assign(KEY_GUIDE)

def OK_click():
    assign(KEY_OK)

def left_click():
    assign(KEY_LEFT_BUTTON)

def right_click():
    assign(KEY_RIGHT_BUTTON)

def up_click():
    assign(KEY_UP_BUTTON)

def down_click():
    assign(KEY_DOWN_BUTTON)

def red_click():
    assign(KEY_RED)

def green_click():
    assign(KEY_GREEN)

def yellow_click():
    assign(KEY_YELLOW)

def blue_click():
    assign(KEY_BLUE)

def rewind_click():
    assign(KEY_REWIND)

def play_click():
    assign(KEY_PLAY)

def forward_click():
    assign(KEY_FAST_FORWARD)

def record_click():
    assign(KEY_RECORD)

def pause_click():
    assign(KEY_PAUSE)

def stop_click():
    assign(KEY_STOP)

def previous_remote_click():
    global remote_state
    global remote_id
    global remote_name
    
    remote_status.set(rs+"Previous remote")
    remote_id = remote_id_return()
    remote_name = get_remote_name(remote_id)
    a = str(remote_id)
    print(a)
    remote_details.set(rd+"Name : "+str(remote_name)+"\nRemote ID : "+a)
    return

def new_remote_click():
    global remote_state
    global remote_id
    global in_toggle
    global remote_name
    global auto_update_ready
    var.set(r+"\n")
    status.set(s+"\n\n")
    remote_status.set(rs)
    remote_details.set(rd+"\n")
    toggle_status.set(ts+"\n\n")
    edit_status.set(es+"\n")
    auto_update_status.set(au+"\n\n")
    keys_display.set(kd+"\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
    in_toggle = None
    auto_update_ready = False
    check = list()

    remote_status.set(rs+"New remote")
    remote_id = remote_id_return()
    remote_id = remote_id +1
    remote_name = get_new_remote_name()
    if(remote_name == ""):
        remote_details.set(rd+"Enter remote name")
        status.set(s+"Enter remote name\n")
        return
    remote_details.set(rd+"Name : "+remote_name+"\nRemote ID : "+str(remote_id))
    return

def add_key_click():
    print("Add Key")
    global f
    f.focus_set()
    global auto_update_ready
    global remote_id

    if auto_update_ready == True:
        key_id_s = get_key_id()
        if(key_id_s == ""):
            edit_status.set(es+"Enter the Key_ID")
            return
        key_id = int(key_id_s,10)
        assign(key_id)
        edit_status.set(es+"key "+str(key_names[key_id])+" added.")
        return
    else:
        edit_status.set(es+"No auto update found")
        return

def freq_click():
    global frequency
    if(remote_id == None):
        status.set(s+"SELECT A REMOTE...\n\n")
        return
    status.set(s+"PRESS ANY KEY \n\n")
    frequency = freq()
    x = "%.3f"%(frequency/1000)
    print(x)
    var.set(r+"The frequency is "+x+"KHz\n\n")

def remove_key_click():
    print("Remove key")
    global f
    f.focus_set()
    global auto_update_ready
    global remote_id

    if auto_update_ready == True:
        key_id_s = get_key_id()
        if(key_id_s == ""):
            edit_status.set(es+"Enter the Key_ID")
            return
        key_id = int(key_id_s,10)
        delete_key(remote_id,key_id)
        edit_status.set(es+"key "+str(key_names[key_id])+" removed.")
        return
    else:
        edit_status.set(es+"No auto update found")
        return

def popup_():
    global r_id
    global LB
    global orid
    if(len(orid)==1):
        get()
        return
    win = Toplevel()
    win.wm_title("select")
    win.geometry("150x198")
    l= Label(win, text="select the remote")
    l.grid(row=0, column=0)
    LB = Listbox(win)
    LB.place(x=10,y=50)
    
    button_bonus = Button(win,text="OK", command= get)
    button_bonus.place(x=10,y=20)
    for i in range(len(orid)):
        m = str(orid[i])
        print(i,"  ",m)
        LB.insert(END,m)
    LB.activate(0)

def get():
    global LB
    global o_remote_id
    if(len(orid)==1):
        o_remote_id = orid[0]
    else:
        o_remote_id = LB.get(LB.curselection())
    print(o_remote_id)
    auto_update(o_remote_id)


def auto_update(o_remote_id):
    global auto_update_ready
    global remote_id
    global protocol_id
    if auto_update_ready == True and o_remote_id != None:
        auto_update_status.set(au+"A remote with the codes is found\n"+"The data for this remote can be automatically completed")
        auto_complete(remote_id,o_remote_id,protocol_id)
        auto_update_status.set(au+"....THE REMOTE IS UPDATED....")
        status.set(s+"....THE REMOTE IS UPDATED....\n")
        existing_remote_update(remote_id,o_remote_id)
        return
    else:
        auto_update_status.set(au+"No remote found")
        return


def auto_update_click():
    print("auto update clicked")
    global auto_update_ready
    global remote_id
    global o_remote_id
    global protocol_id
    global orid

    if auto_update_ready == True:
        print(len(orid))
        popup_()  
    

def update_new_remote_click():
    auto_update_status.set(au+"\n\n")
    var.set(r+"\n\n")
    status.set(s+"The remote has been recorded in the database\n\n")
    keys_display.set(kd+"\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
    print('The remote has been saved in the database')

    
B_freq = Button(top,text="Calculate Frequency",relief = 'flat' ,command = freq_click,height = 1,width = 33)
B_freq.place(x=19,y=10)

B_power = Button(top,text="power",relief = 'flat' ,command = power_click,height = 1,width = 8)
B_power.place(x=18,y=45)

B_info = Button(top,text="info",relief = 'flat' ,command = info_click,height = 1,width = 8)
B_info.place(x=109,y=45)

B_mute = Button(top,text="mute",relief = 'flat' ,command = mute_click,height = 1,width = 8)
B_mute.place(x=196,y=45)

B_1 = Button(top,text="1",relief = 'flat' ,command = one_click,height = 2,width = 8)
B_1.place(x=18,y=80)

B_2 = Button(top,text="2",relief = 'flat' ,command = two_click,height = 2,width = 8)
B_2.place(x=109,y=80)

B_3 = Button(top,text="3",relief = 'flat' ,command = three_click,height = 2,width = 8)
B_3.place(x=196,y=80)

B_4 = Button(top,text="4",relief = 'flat' ,command = four_click,height = 2,width = 8)
B_4.place(x=18,y=129)

B_5 = Button(top,text="5",relief = 'flat' ,command = five_click,height = 2,width = 8)
B_5.place(x=109,y=129)

B_6 = Button(top,text="6",relief = 'flat' ,command = six_click,height = 2,width = 8)
B_6.place(x=196,y=129)

B_7 = Button(top,text="7",relief = 'flat' ,command = seven_click,height = 2,width = 8)
B_7.place(x=18,y=177)

B_8 = Button(top,text="8",relief = 'flat' ,command = eight_click,height = 2,width = 8)
B_8.place(x=109,y=177)

B_9 = Button(top,text="9",relief = 'flat' ,command = nine_click,height = 2,width = 8)
B_9.place(x=196,y=177)

B_0 = Button(top,text="0",relief = 'flat' ,command = zero_click,height = 2,width = 8)
B_0.place(x=109,y=223)

B_vol_up = Button(top,text="vol up",relief = 'flat' ,command = vol_up_click,height = 3,width = 6)
B_vol_up.place(x=18,y=223)

B_vol_down = Button(top,text="vol down",relief = 'flat' ,command = vol_down_click,height = 3,width = 6)
B_vol_down.place(x=18,y=282)

B_ch_up = Button(top,text="ch up",relief = 'flat' ,command = ch_up_click,height = 3,width = 6)
B_ch_up.place(x=210,y=223)

B_ch_down = Button(top,text="ch down",relief = 'flat' ,command = ch_down_click,height = 3,width = 6)
B_ch_down.place(x=210,y=282)

B_back = Button(top,text="back",relief = 'flat' ,command = back_click,height = 1,width = 8)
B_back.place(x=109,y=280)

B_exit = Button(top,text="exit",relief = 'flat' ,command = exit_click,height = 1,width = 8)
B_exit.place(x=109,y=310)

B_menu = Button(top,text="menu",relief = 'flat' ,command = menu_click,height = 1,width = 8)
B_menu.place(x=18,y=345)

B_source = Button(top,text="source",relief = 'flat' ,command = source_click,height = 1,width = 8)
B_source.place(x=109,y=345)

B_options = Button(top,text="options",relief = 'flat' ,command = options_click,height = 1,width = 8)
B_options.place(x=196,y=345)

B_previous = Button(top,text="previous",relief = 'flat' ,command = previous_click,height = 2,width = 4)
B_previous.place(x=18,y=380)

B_next = Button(top,text="next",relief = 'flat' ,command = next_click,height = 2,width = 4)
B_next.place(x=225,y=380)

B_language = Button(top,text="language",relief = 'flat' ,command = language_click,height = 2,width = 4)
B_language.place(x=18,y=425)

B_guide = Button(top,text="guide",relief = 'flat' ,command = guide_click,height = 2,width = 4)
B_guide.place(x=225,y=425)

B_OK = Button(top,text="OK",relief = 'flat' ,command = OK_click,height = 1,width = 4)
B_OK.place(x=120,y=410)

B_up = Button(top,text="up",relief = 'flat' ,command = up_click,height = 1,width = 4)
B_up.place(x=120,y=380)

B_down = Button(top,text="down",relief = 'flat' ,command = down_click,height = 1,width = 4)
B_down.place(x=120,y=440)

B_left = Button(top,text="<",relief = 'flat' ,command = left_click,height = 5,width = 1)
B_left.place(x=80,y=380)

B_right = Button(top,text=">",relief = 'flat' ,command = right_click,height = 5,width = 1)
B_right.place(x=185,y=380)

B_red = Button(top,text="",relief = 'flat' ,command = red_click,height = 2,width = 4,bg='red')
B_red.place(x=18,y=480)

B_green = Button(top,text="",relief = 'flat' ,command = green_click,height = 2,width = 4,bg = 'green')
B_green.place(x=88,y=480)

B_yellow = Button(top,text="",relief = 'flat' ,command = yellow_click,height = 2,width = 4,bg = 'yellow')
B_yellow.place(x=157,y=480)

B_blue = Button(top,text="",relief = 'flat' ,command = blue_click,height = 2,width = 4,bg = 'blue')
B_blue.place(x=225,y=480)

B_rewind = Button(top,text="<<",relief = 'flat' ,command = rewind_click,height = 1,width = 8)
B_rewind.place(x=18,y=543)

B_play = Button(top,text="play",relief = 'flat' ,command = play_click,height = 1,width = 8)
B_play.place(x=109,y=543)

B_forward = Button(top,text=">>",relief = 'flat' ,command = forward_click,height = 1,width = 8)
B_forward.place(x=196,y=543)

B_record = Button(top,text="record",relief = 'flat' ,command = record_click,height = 1,width = 8)
B_record.place(x=18,y=573)

B_pause = Button(top,text="pause",relief = 'flat' ,command = pause_click,height = 1,width = 8)
B_pause.place(x=109,y=573)

B_stop = Button(top,text="stop",relief = 'flat' ,command = stop_click,height = 1,width = 8)
B_stop.place(x=196,y=573)

B_new_remote = Button(top,text="new remote",relief = 'flat' ,command = new_remote_click,height = 2,width = 20)
B_new_remote.place(x=432,y=220)

B_previous_remote = Button(top,text="previous remote",relief = 'flat' ,command = previous_remote_click,height = 2,width = 20)
B_previous_remote.place(x=432,y=265)

B_add_key = Button(top,text="ADD KEY",relief = 'flat' ,command = add_key_click,height = 2,width = 17)
B_add_key.place(x=301,y=390)

B_remove_key = Button(top,text="REMOVE KEY",relief = 'flat' ,command = remove_key_click,height = 2,width = 17)
B_remove_key.place(x=450,y=390)

B_auto_update = Button(top,text="UPDATE NEW REMOTE",relief = 'flat' ,command = update_new_remote_click,height = 1,width = 39)
B_auto_update.place(x=301,y=540)

B_auto_update = Button(top,text="AUTO UPDATE",relief = 'flat' ,command =  auto_update_click ,height = 1,width = 39)
B_auto_update.place(x=301,y=580)

B_close_form = Button(top,text="CLOSE REMOTE",relief = 'flat' ,command = top.destroy,height = 1,width = 79)
B_close_form.place(x=18,y=620)
top.mainloop()


















