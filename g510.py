import time
from machine import UART, Pin
from ADC_DATA import read_ADC_PORTS
import sys

# Configurarea pinilor GPIO
GPIO18 = Pin(18, Pin.OUT)
GPIO46 = Pin(46, Pin.OUT)
GPIO9  = Pin( 9, Pin.IN) #RING
GPIO10 = Pin(10, Pin.IN) #CTS_MODEM
GPIO11 = Pin(11, Pin.IN) #RTS_MODEM
GPIO12 = Pin(12, Pin.IN) #DCD_MODEM

uart = 0
status1 = 0 # g510_last_error_1
status2 = 0 # g510_last_error_2

def sleep_milliseconds(ms):
    time.sleep(ms / 1000.0)


def UART_init():
    global uart
    uart = UART(1, baudrate=9600, tx=47, rx=21)
    uart.init(9600, bits=8, parity=None, stop=1)
    return uart
"""
def read_uart_data():
    UART_buffer = ""
    while uart.any():  # Asigura ca citim toate datele disponibile
        data = uart.read()
        if data:
            UART_buffer += data.decode("utf-8")
    return UART_buffer
"""

def UART_send_string(string):
    uart.write(string)  



def read_uart_data(lines_to_be_read):
    UART_buffer = ""
    timeout = 100
    while timeout and lines_to_be_read:
        while uart.any():  # Asigura ca citim toate datele disponibile
            data = uart.read()
            print(data)
            if data:
                try:
                    decoded_data = data.decode("utf-8")
                    UART_buffer += decoded_data
                    print(f"Data received: {decoded_data}")
                except Exception as e:
                    print(f"Decoding error: {e}, Data: {data}")
                lines_to_be_read -= 1
        timeout -= 1
        # print("sleep")
        sleep_milliseconds(15)
    
    detected_line_1 = False
    detected_line_2 = False
    detected_line_3 = False
    detected_line_4 = False
    detected_line_5 = False
    detected_line_6 = False
    
    line_feed_counter = 0
    #force_exit_delay_function = False
    
    for element in UART_buffer:
        print(element)
        #print(line_feed_counter)
        if element == '\x0a':
            line_feed_counter += 1

        if line_feed_counter == 2:
            detected_line_1 = True
            #force_exit_delay_function = True
            
        elif line_feed_counter == 4:
            detected_line_2 = True
            #force_exit_delay_function = True
            
        elif line_feed_counter == 6:
            detected_line_3 = True
            #force_exit_delay_function = True
            
        elif line_feed_counter == 8:
            detected_line_4 = True
            #force_exit_delay_function = True
            
        elif line_feed_counter == 10:
            detected_line_5 = True
            #force_exit_delay_function = True
            
        elif line_feed_counter == 12:
            detected_line_6 = True
            #force_exit_delay_function = True
    print(UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6)
           
    return UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6

def G510_poweron():
    # Enable battery, BATT_ON_OFF on 1
    GPIO46.value(1)   
    # Turn on G510, PWON-MSP on 1, PWON on 0
    GPIO18.value(1)
    
    sleep_milliseconds(800) #keep power on pulled low for 800 milliseconds
    
    # PWON-MSP on 0
    GPIO18.value(0)  
    
    sleep_milliseconds(800) #keep power on pulled low for 800 milliseconds
    UART_send_string('AT\r\n')
    sleep_milliseconds(1000) #keep power on pulled low for 1 second
    print("Am pornit")
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(1)

    #return 0

    _,_,value_VBAT_GPRS,_ = read_ADC_PORTS()
    # print("value_VBAT_GPRS = " + str(value_VBAT_GPRS))
    if value_VBAT_GPRS < 2.7:
        return 1
    else:
        return 0



def G510_poweroff():
    #power off G510 , PWON-MSP on 1, PWON on 0
    GPIO18.value(1)  
    
    sleep_milliseconds(3000) #keep power on pulled low for 3 seconds
    
    #PWON-MSP on 0, PWON on 1
    GPIO18.value(0)  
    sleep_milliseconds(1000) #keep power on pulled low for 1 second
    GPIO46.value(0)  
    print("Am oprit")

def G510_read_signal_strength():
    print("Entering G510_read_signal_strength")
    global UART_buffer
    UART_buffer = "" 
    timeout = 40
    UART_send_string("AT+CSQ?\r\n")
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6 = read_uart_data(2)
    print(UART_buffer)
    
    if detected_line_2 is True and ("\r\nOK\r\n" in UART_buffer and "\r\n+CSQ:" in UART_buffer):
        return 0, UART_buffer  #result is located from UART_buffer[16] to UART_buffer[UART_index-9] for AT+CSQ
    else:
        return 1, UART_buffer  
    
def G510_read_GSM_Status():
    print("Entering G510_read_GSM_Status")
    UART_send_string('AT+CREG?\r\n')
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6 = read_uart_data(2)
    print(UART_buffer)
    
    if detected_line_1 is False and detected_line_2 is False:
        return 1, None
    elif "\r\nOK\r\n" in UART_buffer:
        # found OK on second line, processing command response
        # 0 Not registered, and the ME is not currently searching for a new operator to which to register.
        if "\r\n+CREG: 0,0" in UART_buffer or "\r\n+CREG: 2,0" in UART_buffer:
            return 3, None
        # 1 Registered, home network.
        elif "\r\n+CREG: 0,1" in UART_buffer or "\r\n+CREG: 2,1" in UART_buffer:
            return 0, UART_buffer
        # 2 Not registered, but the ME is currently searching for a new operator to which to register.
        elif "\r\n+CREG: 0,2" in UART_buffer or "\r\n+CREG: 2,2" in UART_buffer:
            return 4, None
        # 3 Registration denied.
        elif "\r\n+CREG: 0,3" in UART_buffer or "\r\n+CREG: 2,3" in UART_buffer:
            return 5, None
        # 4 Unknown.
        elif "\r\n+CREG: 0,4" in UART_buffer or "\r\n+CREG: 2,4" in UART_buffer:
            return 6, None
        # 5 Registered, roaming.
        elif "\r\n+CREG: 0,5" in UART_buffer or "\r\n+CREG: 2,5" in UART_buffer:
            return 2, UART_buffer
        else:
            return 255, None  # unknown error
    else:
        return 255, None

def G510_de_register_network():
    print("Entering G510_de_register_network")
    UART_send_string("AT+COPS=2\r\n")
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(1)
    
    if detected_line_1 is False:
        return 1
    
    if "\r\nOK\r\n" in UART_buffer:
        return 0
    else:
        return 255

def G510_set_verbose():
    print("Entering G510_set_verbose")
    UART_send_string("AT+CMEE=2\r\n")
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(2)
    if detected_line_1 is True and "\r\nOK\r\n" in UART_buffer:
        return 0
    else:
        return 1
    

def G510_set_mstart():
    print("Entering G510_set_mstart")
    UART_send_string("AT+MSTART=0,0\r\n")
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    print("Timeout is: " + str(timeout))
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(2)
    
    if detected_line_1 is True and "\r\nOK\r\n" in UART_buffer:
        return 0
    else:
        return 1
    
def G510_set_DCD_mode():
    print("Entering G510_set_DCD_mode")
    UART_send_string("AT&C2\r\n")  
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(1)
    
    if detected_line_1 is False:
        return 1
    elif "\r\nOK\r\n" in UART_buffer:
        return 0
    elif "\r\n+CME ERROR:" in UART_buffer:
        if "\r\n+CME ERROR: parameters are invalid\r\n" in UART_buffer or "\r\n+CME ERROR: 53\r\n" in UART_buffer:
            return 3
        else:
            return 255
    elif "\r\nERROR\r\n" in UART_buffer:
        return 2  # ERROR Message, verbose mode = 0 , no details about this error
    else:
        return 255  # unknown error
    
def G510_set_PIN():
    print("Entering G510_set_PIN")
    UART_send_string('AT+CPIN="5018"\r\n')  
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(2)
    
    if detected_line_1 is False:
        return 1
    elif "\r\nOK\r\n" in UART_buffer:
        return 0
    elif "\r\n+CME ERROR:" in UART_buffer:
        if ("\r\n+CME ERROR: SIM not inserted\r\n" in UART_buffer) or ("\r\n+CME ERROR: 10\r\n" in UART_buffer):
            return 3
        elif ("\r\n+CME ERROR: SIM PIN required\r\n" in UART_buffer) or ("\r\n+CME ERROR: 11\r\n" in UART_buffer):
            return 4
        elif ("\r\n+CME ERROR: SIM PUK required\r\n" in UART_buffer) or ("\r\n+CME ERROR: 12\r\n" in UART_buffer):
            return 5
        elif ("\r\n+CME ERROR: SIM failure\r\n" in UART_buffer) or ("\r\n+CME ERROR: 13\r\n" in UART_buffer):
            return 6
        elif ("\r\n+CME ERROR: SIM busy\r\n" in UART_buffer) or ("\r\n+CME ERROR: 14\r\n" in UART_buffer):
            return 7
        elif ("\r\n+CME ERROR: SIM wrong\r\n" in UART_buffer) or ("\r\n+CME ERROR: 15\r\n" in UART_buffer):
            return 8
        elif ("\r\n+CME ERROR: Incorrect password\r\n" in UART_buffer) or ("\r\n+CME ERROR: 16\r\n" in UART_buffer):
            return 9
        elif ("\r\n+CME ERROR: SIM PIN2 required\r\n" in UART_buffer) or ("\r\n+CME ERROR: 17\r\n" in UART_buffer):
            return 10
        elif ("\r\n+CME ERROR: SIM PUK2 required\r\n" in UART_buffer) or ("\r\n+CME ERROR: 18\r\n" in UART_buffer):
            return 12
        elif ("\r\n+CME ERROR: Operation not allowed\r\n" in UART_buffer) or ("\r\n+CME ERROR: 3\r\n" in UART_buffer):
            return 13
        else:
            return 255
    elif "\r\nERROR\r\n" in UART_buffer:
        return 2  # ERROR Message, verbose mode = 0 , no details about this error
    else:
        return 255  # unknown error


def G510_read_pin_status():
    print("Entering G510_read_pin_status")
    UART_send_string("AT+CPIN?\r\n")  
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(2)
    
    if detected_line_1 is False:
        return 1
    elif "\r\n+CPIN:" in UART_buffer:
        # we got a CPIN result on first line, wait for OK and then process the CPIN result 
        if  detected_line_2 is False:
            return 1
        elif "\r\n+CPIN: READY\r\n" in UART_buffer:
            return 0
        elif "\r\n+CPIN: SIM PIN\r\n" in UART_buffer:
            return 14
        elif "\r\n+CPIN: SIM PUK\r\n" in UART_buffer:
            return 15
        elif "\r\n+CPIN: SIM PIN2\r\n" in UART_buffer:
            return 16
        elif "\r\n+CPIN: SIM PUK2\r\n" in UART_buffer:
            return 17
        else:
            return 255
    elif "\r\n+CME ERROR:" in UART_buffer:
        if ("\r\n+CME ERROR: SIM not inserted\r\n" in UART_buffer or 
            "\r\n+CME ERROR: 10\r\n" in UART_buffer):
            return 3
        elif ("\r\n+CME ERROR: SIM PIN required\r\n" in UART_buffer or 
              "\r\n+CME ERROR: 11\r\n" in UART_buffer):
            return 4
        elif ("\r\n+CME ERROR: SIM PUK required\r\n" in UART_buffer or 
              "\r\n+CME ERROR: 12\r\n" in UART_buffer):
            return 5
        elif ("\r\n+CME ERROR: SIM failure\r\n" in UART_buffer or 
              "\r\n+CME ERROR: 13\r\n" in UART_buffer):
            return 6
        elif ("\r\n+CME ERROR: SIM busy\r\n" in UART_buffer or 
              "\r\n+CME ERROR: 14\r\n" in UART_buffer):
            return 7
        elif ("\r\n+CME ERROR: SIM wrong\r\n" in UART_buffer or 
              "\r\n+CME ERROR: 15\r\n" in UART_buffer):
            return 8
        elif ("\r\n+CME ERROR: Incorrect password\r\n" in UART_buffer or 
              "\r\n+CME ERROR: 16\r\n" in UART_buffer):
            return 9
        elif ("\r\n+CME ERROR: SIM PIN2 required\r\n" in UART_buffer or 
              "\r\n+CME ERROR: 17\r\n" in UART_buffer):
            return 10
        elif ("\r\n+CME ERROR: SIM PUK2 required\r\n" in UART_buffer or 
              "\r\n+CME ERROR: 18\r\n" in UART_buffer):
            return 12
        elif ("\r\n+CME ERROR: Operation not allowed\r\n" in UART_buffer or 
              "\r\n+CME ERROR: 3\r\n" in UART_buffer):
            return 13
        else:
            return 255
    elif "\r\nERROR\r\n" in UART_buffer:
        return 2  # ERROR Message, verbose mode = 0 , no details about this error
    else:
        return 255
    
def G510_read_GPRS_Status():
    print("Entering G510_read_GPRS_Status")
    
    UART_send_string("AT+CGREG?\r\n")  
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(2)
    
    if detected_line_1 is False or detected_line_2 is False:
        return 1
    
    if "\r\nOK\r\n" in UART_buffer:
        # found OK on second line, processing command response
        # 0 Not registered, and the ME is not currently searching for a new operator to which to register.
        if "\r\n+CGREG: 0,0" in UART_buffer or "\r\n+CGREG: 2,0" in UART_buffer:
            return 3
        # 1 Registered, home network.
        elif "\r\n+CGREG: 0,1" in UART_buffer or "\r\n+CGREG: 2,1" in UART_buffer:
            return 0
        # 2 Not registered, but the ME is currently searching for a new operator to which to register.
        elif "\r\n+CGREG: 0,2" in UART_buffer or "\r\n+CGREG: 2,2" in UART_buffer:
            return 4
        # 3 Registration denied.
        elif "\r\n+CGREG: 0,3" in UART_buffer or "\r\n+CGREG: 2,3" in UART_buffer:
            return 5
        # 4 Unknown.
        elif "\r\n+CGREG: 0,4" in UART_buffer or "\r\n+CGREG: 2,4" in UART_buffer:
            return 6
        # 5 Registered, roaming.
        elif "\r\n+CGREG: 0,5" in UART_buffer or "\r\n+CGREG: 2,5" in UART_buffer:
            return 2
        else:
            return 255  # unknown error
    else:
        return 255
    

def G510_read_ICCID():
    print("Entering g510_read_iccid")
    # the SIM must be initialized to read ICCID, no PIN required
    UART_send_string("AT+CCID?\r\n")  
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(2)
    
    if detected_line_1 is False:
        return 1, None
    elif "\r\n+CCID:" in UART_buffer:
        if detected_line_2 is False:
            return 1, None
        elif "\r\nOK\r\n" in UART_buffer:
            return 0, UART_buffer  # result is located from UART_buffer[18] to UART_buffer[37]
        else:
            return 255, None
    elif "\r\n+CME ERROR:" in UART_buffer:
        # +CME ERROR: Unknown error
        return 3, None  # unimplemented CMEE Error
    elif "\r\nERROR\r\n" in UART_buffer:
        return 2, None  # ERROR Message, verbose mode = 0 , no details about this error
    else:
        return 255, None
    
def G510_connect_to_APN_string(data):
    print("Entering G510_connect_to_APN_string")
    UART_send_string(data)  
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(2)

    if not detected_line_1:
        return 1
    elif "\r\nOK\r\n" in UART_buffer:
        timeout = 1510  # the documentation recommends waiting 150 s for context activation
        while not detected_line_2 and timeout != 0:  # wait for line 2
            sleep_milliseconds(100)
            timeout -= 1

        if timeout == 0:
            return 1
        if "\r\n+MIPCALL:" in UART_buffer:
            return 0
        else:
            return 255  # unknown error
    elif "\r\n+CME ERROR:" in UART_buffer:
        if ("\r\n+CME ERROR: Operation not allowed\r\n" in UART_buffer or
                "\r\n+CME ERROR: 3\r\n" in UART_buffer):
            return 3
        if ("\r\n+CME ERROR: SIM PIN required\r\n" in UART_buffer or
                "\r\n+CME ERROR: 11\r\n" in UART_buffer):
            return 4
        if ("\r\n+CME ERROR: Unknown error\r\n" in UART_buffer or
                "\r\n+CME ERROR: 282\r\n" in UART_buffer):
            return 5
        else:
            return 6  # unimplemented cmee error
    elif "\r\nERROR\r\n" in UART_buffer:
        return 2  # ERROR Message, verbose mode = 0 , no details about this error
    else:
        return 255

def G510_open_socket_string(data):
    print("Entering G510_open_socket_string")
    UART_send_string(data)  
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(2)

    
    if not detected_line_1:
        return 1
    elif "\r\nOK\r\n" in UART_buffer:
        if detected_line_2 is False:
            return 1
        
        if "\r\n+MIPOPEN: 1,1" in UART_buffer:
            return 0
        elif "\r\n+MIPSTAT: 1,1\r\n" in UART_buffer:
            return 6
        else:
            return 255  # unknown error
    elif "\r\n+TCPIP ERROR:" in UART_buffer:
        if "\r\n+TCPIP ERROR: TCPIP mipcall not active\r\n" in UART_buffer or "\r\n+TCPIP ERROR: 631\r\n" in UART_buffer:
            return 3
        elif "\r\n+TCPIP ERROR: TCPIP socket used\r\n" in UART_buffer or "\r\n+TCPIP ERROR: 617\r\n" in UART_buffer:
            return 4
        else:
            return 5  # unimplemented tcpip error
    elif "\r\nERROR\r\n" in UART_buffer:
        return 2  # ERROR Message, verbose mode = 0 , no details about this error
    else:
        return 255

def num_to_hex_string(num, length):
    # Convert the number to a hexadecimal string and remove the '0x' prefix
    if isinstance(num, str):
        hex_string = hex(ord(num))[2:].upper()
    elif isinstance(num, int):
        hex_string = hex(num)[2:].upper()
    else:
        raise TypeError("it must be string or integer")
    # Calculate the padding needed to reach 8 characters
    padding_length = length - len(hex_string)
    # Create the padded string
    padded_hex_string = '0' * padding_length + hex_string
    return padded_hex_string


def process_response_from_server_extended(timeout, UART_buffer, detected_line_1):
    print("Entering process_response_from_server_extended")
    
#     detected_line_1 = False
#     while timeout and not detected_line_1:
#         sleep_milliseconds(100)
#         timeout -= 100
#         UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(1)
#     print("timout = " + str(timeout))
#     print(UART_buffer)

    print(UART_buffer)
    if detected_line_1 is False:
        return 1
    elif "\r\n+MIPRTCP: 1,0,0206" in UART_buffer:
        return 0  # Incoming packet from server, packet type 0x02 server response type, server response 0x06 ACK
    else:
        return 2  # Did not receive expected response from server
    

def process_response_from_mip_send(UART_buffer, detected_line_1, detected_line_2):
    
    if detected_line_1 is False:
        return 1
    elif "\r\n+MIPSEND:" in UART_buffer:
        if detected_line_2 is False:
            return 1
        elif "\r\nOK\r\n" in UART_buffer:
            if "\r\n+MIPSEND: 1,0" in UART_buffer:
                return 0  # 0 - Success
            elif "\r\n+MIPSEND: 1,1" in UART_buffer:
                return 2  # buffer is full
            else:
                return 255  # unknown error
        else:
            return 255  # unknown error
    elif "\r\n+TCPIP ERROR: TCPIP invalid operation\r\n" in UART_buffer:
        return 4  # No TCP socket opened
    elif "\r\nERROR\r\n" in UART_buffer:
        return 3  # ERROR Message, verbose mode = 0 , no details about this error
    else:
        print("\n\n=" + UART_buffer + "= \n\n")
        return 259  # unknown error
    
def mip_push():
    # Send AT command for MIPPUSH
    UART_send_string("AT+MIPPUSH=1\r\n")  
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(2)
    
    if detected_line_1 is False:
        return None, None, 1
    elif "\r\n+MIPPUSH:" in UART_buffer:
        if detected_line_2 is False:
            return None, None, 1
        elif "\r\nOK\r\n" in UART_buffer:
            # received OK, process MIPPUSH status
            if "\r\n+MIPPUSH: 1,0\r\n" in UART_buffer:
                return UART_buffer, detected_line_1,0  # 0 - Success
            elif "\r\n+MIPPUSH: 1,1\r\n" in UART_buffer:
                return None, None,3  # 1 - socket is flowed off // network busy
            elif "\r\n+MIPPUSH: 1,2\r\n" in UART_buffer:
                return None, None,4  # 2 - there is no data in socket to send
            else:
                return None, None,255  # unknown error
        else:
            return None, None,255  # unknown error
    elif "\r\n+TCPIP ERROR: TCPIP invalid operation\r\n" in UART_buffer:
        return None, None,5  # No TCP socket opened
    elif "\r\nERROR\r\n" in UART_buffer:
        return None, None,2  # ERROR Message, verbose mode = 0 , no details about this error
    else:
        return None, None,255  # unknown error
    
def mip_push_retry(retry):
    result = 0
    for i in range(retry):
        UART_buffer, detected_line_1, result = mip_push() 
        if result != 3:
            return UART_buffer, detected_line_1, result  # network is not busy return the result of mip push command
        
        # Wait 500 ms between retry attempts
        sleep_milliseconds(500)
    
    return None, None, 3  # failed to send data network is still busy after all attempts

def send_ID_packet():
    print("Entering send_ID_packet")
    timeout = 40
    serial_number = 939553298
    packet_type = 0x01 #ID packet
    percentage = 0
    #length = sys.getsizeof(packet_type)+sys.getsizeof(serial_number)+sys.getsizeof(g510_last_error_1)+sys.getsizeof(g510_last_error_2)+sys.getsizeof(percentage)
    length = 9
    #tmp = (not_updated_user_count * 1000) // user_count
    percentage = 22
    
    string = "AT+MIPSEND=1,\""
    string += num_to_hex_string(length, 4)
    string += num_to_hex_string(packet_type, 2)
    string += num_to_hex_string(serial_number, 8)
    string += num_to_hex_string(status1, 2)
    string += num_to_hex_string(status2, 2)
    string += num_to_hex_string(percentage, 4)
    string += "\"\r\n"
    
    print("\n\n\n\n String = " + string)
    UART_send_string(string)  
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(5)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(2)
    
    print("\n\n\n send id aici " + UART_buffer + " pana aici \n\n\n\n\n")
    
    if process_response_from_mip_send(UART_buffer, detected_line_1, detected_line_2)!=0 : 
        return 1
    
    UART_buffer, detected_line_1, return_value = mip_push_retry(6)
    if return_value !=0 :
        return 2

    #expecting server response in mininum 1 s, enough time to clean the rx buffer
    timeout = 600;
    a = process_response_from_server_extended(timeout, UART_buffer, detected_line_1)
    if a !=0:
        print("process_response_from_server_extended = " + str(a)) 
        return None, None, 3

    return 0

def G510_read_registered_operator():
    # PLMN UART_buffer[23:27] add 28 aswell to be compatible with 3 digit MNCs
    print("Entering G510_read_registered_operator")
    UART_send_string("AT+COPS?\r\n")  
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(2)

    if '\r\n+COPS:' not in UART_buffer:
        return 1, None   
    else:
        if '\r\nOK\r\n' in UART_buffer:
            if '\r\n+COPS: 2' in UART_buffer:
                return 4, None # not registered in the network
            elif '\r\n+COPS: 0,0,' in UART_buffer or '\r\n+COPS: 0,2,' in UART_buffer:
                return 0 , UART_buffer # +COPS: 0,0,
            else:
                return 255, None
        elif '\r\n+CME ERROR:' in UART_buffer:
            return 3 , None # unimplemented CMEE Error
        elif '\r\nERROR\r\n' in UART_buffer:
            return 2 , None # ERROR Message, verbose mode = 0, no details about this error

    return 255, None

# 
# AT+GSN?
# 
# +GSN: "869267016819364"
# 
# OK
# 
# AT+CGSN?
# 
# +CGSN: "869267016819364"
# 
# OK

#+CGSN,+GSN - IMEI - 15 digit
def G510_read_IMEI():
    #result is located from UART_buffer[19] to UART_buffer[33] for AT+CGSN
    UART_send_string("AT+GSN?\r\n")  
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(2)
    if (detected_line_2 is not False) and "\r\nOK\r\n" in UART_buffer and "\r\n+GSN:" in UART_buffer:
        return 0, UART_buffer # result is located from UART_buffer[17] to UART_buffer[31] for AT+GSN
    else: 
        return 1, None

# 
# ---------------------- PIN Not Set ---------------------------------------------
# AT+CIMI?
# 
# ERROR
# 
# AT+CIMI?
# 
# +CME ERROR: SIM wrong
# --------------------------------------------------------------------------------
def G510_read_IMSI():
    # the SIM must be initialized and the PIN must be set
    UART_send_string("AT+CIMI?\r\n")  
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(2)
    
    if detected_line_1 is False:
        return 1, None
    else:
        if '\r\n+CIMI:' in UART_buffer:
            if detected_line_2 is False == 0:
                return 1, None 
            else:
                if '\r\nOK\r\n' in UART_buffer:
                    return 0, UART_buffer  # result is located from UART_buffer[18] to UART_buffer[32]
                else:
                    return 255, None
        elif '\r\n+CME ERROR:' in UART_buffer:  # +CME ERROR: SIM wrong
            return 3, None  # unimplemented CMEE Error
        elif '\r\nERROR\r\n' in UART_buffer:
            return 2, None  # ERROR Message, verbose mode = 0, no details about this error
        else:
            return 255, None


def G510_set_COPS_mode(mode):

    # USCI_A0_send_string("AT+COPS=3,2\r") # Commented out
    string = ''
    string += "AT+COPS=3,"
    string += mode
    string += "\r\n"
    UART_send_string(string)  
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(2)
    
    if detected_line_1 is False:
        return 1
    elif "\r\nOK\r\n" in UART_buffer:
        return 0
    elif "\r\n+CME ERROR:" in UART_buffer:
        if "\r\n+CME ERROR: parameters are invalid\r\n" in UART_buffer or \
           "\r\n+CME ERROR: 53\r\n" in UART_buffer:
            return 3
        else:
            return 255
    elif "\r\nERROR\r\n" in UART_buffer:
        return 2  # ERROR Message, verbose mode = 0, no details about this error
    else:
        return 255  # unknown error

def G510_set_CREG_mode(mode):
    
    string = ""
    string += "AT+CREG="
    string += mode
    string += "\r\n"
    UART_send_string(string)
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(1)

    if detected_line_1 == 0:
        return 1
    elif "\r\nOK\r\n" in UART_buffer:
        return 0
    elif "\r\n+CME ERROR:" in UART_buffer:
        if ("\r\n+CME ERROR: parameters are invalid\r\n" in UART_buffer or
            "\r\n+CME ERROR: 53\r\n" in UART_buffer):
            return 3
        else:
            return 255
    elif "\r\nERROR\r\n" in UART_buffer:
        return 2  # ERROR Message, verbose mode = 0 , no details about this error
    else:
        return 255  # unknown error

def process_response_from_server(timeout):
    UART_buffer = ""
    lines_to_be_read = 1
    while timeout and lines_to_be_read:
        while uart.any():  # Asigura ca citim toate datele disponibile
            data = uart.read()
            print(data)
            if data:
                try:
                    decoded_data = data.decode("utf-8")
                    UART_buffer += decoded_data
                    print(f"Data received: {decoded_data}")
                except Exception as e:
                    print(f"Decoding error: {e}, Data: {data}")
                lines_to_be_read -= 1
        timeout -= 1
        sleep_milliseconds(100)
    
    if lines_to_be_read == 0: # detected_line_1 = 1
        return 1
    elif "\r\n+MIPRTCP: 1,0,0206\r\n" in UART_buffer:
        return 0  # Incoming packet from server, packet type 0x02 server response type, server response 0x06 ACK
    else:
        print(" \n\n\n\n\n AICI: " + UART_buffer + " \n\n GATA \n\n\n")
        return 2  # Did not receive expected response from server
        


def G510_send_registration_packet():
    print("Entering G510_send_registration_packet")
    timeout = 40
    length = 0
    object_number = 0xFFFFFFFF
    network_number = 1
    firmware_version_local = '80'
    gsm_operator = ''
    signal_strength = ''
    PLMN = ''
    LAC = ''
    CI = ''
    result = 0

#     length = (1 + 4 + '''sys.getsizeof(user_count)''' + 
#               1 + '''sys.getsizeof(network_number)''' + 16 + 
#               20 + 15 + 15 + 5 + 6 + 4 + 4)
#    length = (1 + 4 + 4 + 1 + 1 + 16 + 20 + 15 + 15 + 5 + 6 + 4 + 4)
    length = 94
    packet_type = 0x06  # extended ID packet

    string = "AT+MIPSEND=1,\""
    string += num_to_hex_string(length,4)
    string += num_to_hex_string(packet_type,2)
    string += num_to_hex_string(object_number,8)
    user_count=9
    string += num_to_hex_string(user_count,4)
    for i in firmware_version_local:
        string += num_to_hex_string(i,2)
    string += num_to_hex_string(network_number,2)

    #----------------------------------------------------------------------------
    for i in range(16):
        gsm_operator = gsm_operator[:i] + '0' + gsm_operator[i+1:]
    result,UART_buffer  = G510_read_registered_operator()
    if result != 0:
        return 2  # failed to read operator, exiting function
    parts = UART_buffer.split('"')
    for i in parts[1]:
        string += num_to_hex_string(i,2)
    #----------------------------------------------------------------------------
    sleep_milliseconds(100)
    result, UART_buffer = G510_read_ICCID()  # result is located from UART_buffer[18] to UART_buffer[37]
    print(" ICCID = " + str(result))
    if result != 0:
        return 3  # failed to read ICCID
    for i in range(18, 38):
        string += num_to_hex_string(UART_buffer[i],2)
    #----------------------------------------------------------------------------
    sleep_milliseconds(100)
    result, UART_buffer = G510_read_IMEI()  # result is located from UART_buffer[17] to UART_buffer[31] for AT+GSN
    if result != 0:
        return 4  # failed to read IMEI
    for i in range(17, 32):
        string += num_to_hex_string(UART_buffer[i],2)
    #----------------------------------------------------------------------------
    sleep_milliseconds(100)
    result, UART_buffer = G510_read_IMSI()  # result is located from UART_buffer[18] to UART_buffer[32]
    if result != 0:
        return 5  # failed to read IMSI
    for i in range(18, 33):
        string += num_to_hex_string(UART_buffer[i],2)
    #----------------------------------------------------------------------------
    sleep_milliseconds(100)
    result, UART_buffer = G510_read_signal_strength()  # result is located from UART_buffer[16] to UART_buffer[USCI_A0_index-9] for AT+CSQ
    if result != 0:
        return 6  # failed to read signal strength
    parts = UART_buffer.split(": ", 1)
    signal_strength = parts[1]
    print("SIGNAL = " + signal_strength)
    for i in range(5):
        string += num_to_hex_string(signal_strength[i],2)
    #----------------------------------------------------------------------------

    string += '\"\r\n'
    print("\n\n\n\n " + string +  "\n\n\n\n\n")
    UART_send_string(string)
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(2)

    result = process_response_from_mip_send(UART_buffer, detected_line_1, detected_line_2 )
    if  result != 0:
        print("process = " + str(result))
        return 7

    #----------------------------------------------------------------------------
    # Add MCC MNC LAC and CI
    
    sleep_milliseconds(100)
    result = G510_set_COPS_mode('2')  # set COPS mode to '2' in order to return PLMN
    if result != 0:
        return 8  # failed to COPS mode

    sleep_milliseconds(100)
    result, UART_buffer = G510_read_registered_operator()  # result is located from UART_buffer[23] to UART_buffer[28]
    if result != 0:
        return 9  # failed to PLMN
    PLMN = UART_buffer[23:23+6]

    sleep_milliseconds(100)
    result = G510_set_COPS_mode('0')  # restore COPS mode for normal use
    if result != 0:
        return 10  # failed to COPS mode

    sleep_milliseconds(100)
    result = G510_set_CREG_mode('2')  # set CREG mode to '2' in order to return LAC and CI
    if result != 0:
        return 11  # failed to CREG mode

    sleep_milliseconds(100)
    result, UART_buffer = G510_read_GSM_Status()  # results are located from UART_buffer[23] to UART_buffer[26] (LAC) and from UART_buffer[30] to UART_buffer[33] (CI)
    print("\n\n\n\n UART_buffer = " + UART_buffer + "\n\n\n\n\n\n\n\nEND")
    if result != 0 and result != 2:
        return 12  # failed to LAC and CI
    LAC = UART_buffer[23: 23+4]
    CI = UART_buffer[30: 30+4]

    sleep_milliseconds(100)
    result = G510_set_CREG_mode('0')  # restore COPS mode for normal use
    if result != 0:
        return 13  # failed to CREG mode

    #----------------------------------------------------------------------------

    sleep_milliseconds(100)
    string = ''
    print("\n\n\n\n PLMN= " + PLMN + " LAC=  " + LAC + "  CI=  " + CI + "  \n\n\n\n\n\n")
    string += ("AT+MIPSEND=1,\"")
    for i in range(6):
        string += num_to_hex_string(PLMN[i],2)
    for i in range(4):
        string += num_to_hex_string(LAC[i],2)
    for i in range(4):
        string += num_to_hex_string(CI[i],2)
    string += '\"\r\n'
    
    print("\n\n\n\ CE CAUT ACUM: " + string + "\n\n\nGATA\n\n\n")
    
    UART_send_string(string)
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(2)


    if process_response_from_mip_send(UART_buffer, detected_line_1, detected_line_2) != 0:
        return 14
    
    UART_buffer, detected_line_1, return_value = mip_push_retry(6)
    if return_value != 0:
        return 15
    
    timeout = 600
    a = process_response_from_server(timeout)
    if  a != 0:
        print("/n/n/nA= " + str(a)+ "  " + UART_buffer + "  "+ str(detected_line_1))
        return 16

    return 0

def HEX_to_nibble(hex_char):
    # Convert the hex character to its corresponding integer value
    if '0' <= hex_char <= '9':
        return ord(hex_char) - ord('0')
    elif 'A' <= hex_char <= 'F':
        return ord(hex_char) - ord('A') + 10
    elif 'a' <= hex_char <= 'f':
        return ord(hex_char) - ord('a') + 10
    else:
        raise ValueError("Invalid hex character")


def G510_mip_sets():
    timeout = 40
    UART_send_string("AT+MIPSETS=1,2048,0\r\n")
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6  = read_uart_data(2)

    
    if timeout == 0:
        return 1
    elif "\r\n+MIPSETS: 0\r\n" in UART_buffer:
        # We got a +MIPSETS: 0 on the first line, wait for OK and then return 0
        timeout = 40
        while detected_line_2 == 0 and timeout != 0:
            # Wait for line 2
            sleep_milliseconds(100)
            timeout -= 1
        
        if timeout == 0:
            return 1
        elif "\r\nOK\r\n" in UART_buffer:
            return 0
        else:
            return 255  # Unknown error
    elif ("\r\n+TCPIP ERROR: TCPIP operation not allow\r\n" in UART_buffer) or ("\r\n+TCPIP ERROR: 634\r\n" in UART_buffer):
        return 3
    elif "\r\nERROR\r\n" in UART_buffer:
        return 2  # ERROR Message, verbose mode = 0, no details about this error
    else:
        return 255  # Unknown error
    
def G510_upload_upper_sram():
    # Clear Watchdog Timer (Assuming equivalent is not required in Python)
    
    partial_sram_fragment = user_count % 511
    timeout = 40
    packet_type = 0x07  # upper SRAM fragment packet

    # Clear and prepare buffers
    string += 'AT+MIPSEND=1,"'
    
    length = 5 #len(packet_type.to_bytes(1, 'big')) + (4 * partial_sram_fragment)
    
    string += num_to_hex_string(length, 4)
    string += num_to_hex_string(packet_type, 2)
    string += ('"\r\n')
    UART_send_string(string)
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6 = read_uart_data(2)


    if process_response_from_mip_send(timeout) != 0:
        return 11

    for j in range(partial_sram_fragment):
        load_upper_sram_line(j)

    if mip_push_retry(6) != 0:
        return 12

    timeout = 600

    if process_response_from_server(timeout) != 0:
        return 13

    return 0
    
    
def G510_upload_data():
    full_eeprom_fragments = 0
    partial_eeprom_fragment = 0
    user_count = 4 #made up
    bytes_to_send = (128 + 16) * user_count
    percent = 0
    rslt = 0
    
    
    # Set automatic flush to maximum
    rslt = G510_mip_sets()
    if rslt != 0:
        return 2
    
    # Send extended ID packet
    timeout = 40
    packet_type = 0x03  # extended ID packet
    object_number_p = bytearray(0x1900)  # Assuming the address is a placeholder
    object_number = 0
    #firmware_version_local = firmware_version
    firmware_version_local = '81' #made up
    gsm_operator = ''
    
    for i in range(0, 25, 8):
        object_number |= (object_number_p[i//8] << i)
    
    length = 0
    length = 1 + 4 + 4 + 1 + 1 + 16
    
    string = "AT+MIPSEND=1,\""
    network_number = 15 #made up
    string += num_to_hex_string(length,4)
    string += num_to_hex_string(packet_type,2)
    string += num_to_hex_string(object_number,8)
    string += num_to_hex_string(user_count,2)
    for i in firmware_version_local:
        string += num_to_hex_string(i,2)
    string += num_to_hex_string(network_number,4)
    
    # ----------------------------------------------------------------------------
    sleep_milliseconds(100)
    
    for i in range(16):
        gsm_operator = gsm_operator[:i] + '0' + gsm_operator[i+1:]
    result,UART_buffer  = G510_read_registered_operator()
    if result != 0:
        return 2  # failed to read operator, exiting function
    parts = UART_buffer.split('"')
    for i in parts[1]:
        string += num_to_hex_string(i,2)
    
    # ----------------------------------------------------------------------------
    
    string += ("\"\r\n")
    UART_send_string(string)
    
    timeout = 40 
    while (not uart.any()) and timeout:
        sleep_milliseconds(100)
        timeout -= 1
    
    UART_buffer, detected_line_1, detected_line_2, detected_line_3, detected_line_4, detected_line_5, detected_line_6 = read_uart_data(2)

    
    if process_response_from_mip_send(UART_buffer, detected_line_1, detected_line_2) != 0:
        return 3
    
    if mip_push_retry(6) != 0:
        return 4
    
    timeout = 600
    if process_response_from_server(timeout) != 0:
        return 5
    
    # ----------------------------------------------------------------------------
    
    # Upload upper SRAM
    rslt = G510_upload_upper_sram()
    if rslt != 0:
        return 6
    
    # ----------------------------------------------------------------------------
    
    # Upload lower SRAM
    show_percent(0)
    rslt = G510_upload_sram()
    if rslt != 0:
        return 7
    
    # ----------------------------------------------------------------------------
    
    # Upload upper EEPROM if heatmeter are present in userlist
    # rslt = upload_upper_EEPROM()
    # if rslt != 0:
    #     return 7
    
    # ----------------------------------------------------------------------------
    
    full_eeprom_fragments = user_count // 15
    partial_eeprom_fragment = user_count % 15
    
    if full_eeprom_fragments > 0:
        # Processing full EEPROM fragments
        for i in range(full_eeprom_fragments):
            CLEAR_WDT()
            USCI_A0_clear_buffer()
            USCI_A0_clear_TX_buffer()
            USCI_A0_write_string_to_TX_buffer("AT+MIPSEND=1,\"")
            fragment_counter = i
            length = len(bytes(packet_type)) + len(bytes(fragment_counter)) + (128 * 15)
            packet_type = 0x04  # EEPROM fragment packet
            word_to_HEX_String(length)
            byte_to_HEX_String(packet_type)
            byte_to_HEX_String(fragment_counter)
            USCI_A0_write_string_to_TX_buffer("\"\r\n")
            USCI_A0_send_TX_buffer()
            
            if process_response_from_mip_send(UART_buffer, detected_line_1, detected_line_2) != 0:
                return 8
            
            # Process each EEPROM line inside the full fragment
            offset = i * 15
            for j in range(offset, offset + 15):
                rslt = load_eeprom_line(j)
                if rslt != 0:
                    return 9
            
            if mip_push_retry(6) != 0:
                return 10
            
            USCI_A0_clear_buffer()
            timeout = 600
            if process_response_from_server(timeout) != 0:
                return 11
            
            percent = (((user_count * 16) + ((i + 1) * 128 * 15)) * 100) / bytes_to_send
            show_percent(percent)
        
        if partial_eeprom_fragment > 0:
            CLEAR_WDT()
            USCI_A0_clear_buffer()
            USCI_A0_clear_TX_buffer()
            USCI_A0_write_string_to_TX_buffer("AT+MIPSEND=1,\"")
            fragment_counter = i
            length = len(bytes(packet_type)) + len(bytes(fragment_counter)) + (128 * partial_eeprom_fragment)
            packet_type = 0x04  # EEPROM fragment packet
            word_to_HEX_String(length)
            byte_to_HEX_String(packet_type)
            byte_to_HEX_String(fragment_counter)
            USCI_A0_write_string_to_TX_buffer("\"\r\n")
            USCI_A0_send_TX_buffer()
            
            if process_response_from_mip_send(UART_buffer, detected_line_1, detected_line_2) != 0:
                return 12
            
            # Processing each EEPROM line inside the partial EEPROM part
            offset = i * 15
            for j in range(offset, offset + partial_eeprom_fragment):
                rslt = load_eeprom_line(j)
                if rslt != 0:
                    return 13
            
            if mip_push_retry(6) != 0:
                return 14
            
            USCI_A0_clear_buffer()
            timeout = 600
            if process_response_from_server(timeout) != 0:
                return 15
            
            percent = (((user_count * 16) + (i * 128 * 15) + (128 * partial_eeprom_fragment)) * 100) / bytes_to_send
            show_percent(percent)
    elif partial_eeprom_fragment > 0:
        CLEAR_WDT()
        USCI_A0_clear_buffer()
        USCI_A0_clear_TX_buffer()
        USCI_A0_write_string_to_TX_buffer("AT+MIPSEND=1,\"")
        fragment_counter = 0  # Only one fragment and that one is partial
        length = len(bytes(packet_type)) + len(bytes(fragment_counter)) + (128 * partial_eeprom_fragment)
        packet_type = 0x04  # EEPROM fragment packet
        word_to_HEX_String(length)
        byte_to_HEX_String(packet_type)
        byte_to_HEX_String(fragment_counter)
        USCI_A0_write_string_to_TX_buffer("\"\r\n")
        USCI_A0_send_TX_buffer()
        
        if process_response_from_mip_send(UART_buffer, detected_line_1, detected_line_2) != 0:
            return 16
        
        for j in range(partial_eeprom_fragment):
            rslt = load_eeprom_line(j)
            if rslt != 0:
                return 17
        
        if mip_push_retry(6) != 0:
            return 18
        
        USCI_A0_clear_buffer()
        timeout = 600
        if process_response_from_server(timeout) != 0:
            return 19
        
        percent = (((user_count * 16) + (128 * partial_eeprom_fragment)) * 100) / bytes_to_send
        show_percent(percent)
    
    return 0


def G510_auto_connect_production():
    
    status2 = G510_poweron()
    if status2 != 0:
        return 1 #Failed to power on the module, this might happen if your are using a defective module,
                 #if you forget to connect battery/wall plug or you forget to mount the GPRS module.
    
    sleep_milliseconds(100)
    status2 = G510_set_verbose()
    if(status2 != 0):
        return 2 #Failed to set verbose (sets the Report Mobile Equipment Error to verbose mode), also this might happen if you forget to connect battery/wall plug or you forget to mount the GPRS module.
    
    sleep_milliseconds(100)
    status2 = G510_set_mstart()
    if status2 != 0:
        return 3 #Failed to configure mstart, disables +SIM_ready +AT_READY events
    
    #Waiting for SIM card to initialize and ask for pin
    #---------------------------------------------------------------------------
    for i in range(300):  # wait 30 s
        status2 = G510_read_pin_status()
        if status2 == 14:  # if SIM card is waiting for pin, exit delay loop
            break
        # 1 - timeout ; 3 - SIM not inserted; 6 - SIM failure; 15 - CPIN: SIM PUK; 16 - CPIN: SIM PIN2; 17 - CPIN: SIM PUK2
        elif status2 in [1, 6, 15, 16, 17, 255]:
            return 4
        elif status2 == 3:
            pass  # _NOP()
        sleep_milliseconds(100)
    
    if status2 == 14: # if SIM card is waiting for pin , input pin
        status2 = G510_set_PIN()
        if status2 != 0 :
              return 5 #failed to set pin
    else:
          return 4 #SIM failed to initialize
         
    #Successfully set pin, waiting for network registration
    #----------------------------------------------------------------------------
    for i in range (400): #wait 40 seconds for network registration
          status2 = G510_read_GPRS_Status()
          if (status2 == 0) or (status2==2) :
                  break #registered to network force exit delay loop
          if (status2 == 255):
            return 5
          sleep_milliseconds(100);
    if(status2 != 0) and (status2!=2):
          return 6#failed to register to the GPRS Network
    #----------------------------------------------------------------------------
        
    #Determine SIM card type
    #----------------------------------------------------------------------------
    sleep_milliseconds(100) #to_be_determined
    status2, UART_buffer = G510_read_ICCID()
    if status2 !=0 :
        return 8 # failed to detect SIM Card
   
    if "8943015" in UART_buffer:
        status2 = G510_connect_to_APN_string("AT+MIPCALL=1,\"messtechnik.a1.net\",\"messtechnik\",\"messtechnik\"\r\n");
    if status2 != 0 :
      return 7 # failed to connect to the internet
    else:
        status2 = G510_connect_to_APN_string("AT+MIPCALL=1,\"messtechnik\",\"MTmesstechnik\",\"MTmesstechnik\"\r\n");
    if status2 != 0 :
      return 7 # failed to connect to the internet
    
    # ----------------------------------------------------------------------------
    
    
    #Successfully conected to the internet, connecting to GPRS Server
    #----------------------------------------------------------------------------
    sleep_milliseconds(200) #to_be_determined
    # status2 = G510_open_socket_string("AT+MIPOPEN=1,7000,\"192.168.11.205\",6789,0\r\n");
    status2 = G510_open_socket_string("AT+MIPOPEN=1,7000,\"192.168.11.205\",6789,0\r\n");
    if status2 != 0 :
          return 8 # failed to connect to the GPRS Server
    #----------------------------------------------------------------------------
        
    #Successfully conected to the GPRS Server, sending ID packet
    #----------------------------------------------------------------------------
    sleep_milliseconds(100)#to_be_determined
    status2 = send_ID_packet()
    if status2 != 0:
          return 9 # failed to transmit ID packet
    request_byte = (4 << HEX_to_nibble(UART_buffer[20])) | HEX_to_nibble(UART_buffer[21])
    #----------------------------------------------------------------------------
    if (request_byte & 0x01) !=0 :
        #server is requesting registration packet
        sleep_milliseconds(100) #to_be_determined
        status2 = G510_send_registration_packet()
        print("registration Packet = " + str(status2))
        if status2 != 0 :
              return 10 #failed to transmit registration packet

    #Successfully sent ID packet, uploading dacos data
    #----------------------------------------------------------------------------
    sleep_milliseconds(100)
    status2 = G510_upload_data()
    print(status2)
    if status2 !=0 :
      return 11 #failed to upload dacos data
    #----------------------------------------------------------------------------
    
#"main"
uart = UART_init()
#G510_poweron()
#sleep_milliseconds(10000)
#print(G510_read_signal_strength())
#print(G510_read_GSM_Status())
#print(G510_de_register_network())


status1 = G510_auto_connect_production()
print("PRODUCTION =" + str(status1))

#print(G510_set_verbose())
#print(G510_set_mstart())
#print(G510_set_DCD_mode())

sleep_milliseconds(10000)
G510_poweroff()


   

