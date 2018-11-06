import serial
import numpy as np
from time import sleep


class SR530demo():
    def __init__(self, port, baudrate):
        pass
        self.datasetX = np.sin(np.linspace(0, 10*np.pi, 2500))
        self.datasetY = np.cos(np.linspace(0, 10*np.pi, 2500))
        self.dataN = 0

    def connect(self):
        print('DEMO LIA: connect')

    def measure(self):
        measurement = (self.datasetX[self.dataN], self.datasetY[self.dataN])
        self.dataN = self.dataN + 1
        sleep(0.002)
        return measurement

    def demo_measure_reset(self):
        self.dataN = 0

    def query(self, input):
        print('DEMO LIA: Query made with '+str(input)+', returning something')
        return None

    def set_tc(self, tc):
        print('DEMO LIA: set_tc '+str(tc))

    def set_sens(self, sens):
        print('DEMO LIA: set_sens '+str(sens))

    def send(self, input_string):
        print('DEMO LIA: send '+input_string)

    def close(self):
        print('DEMO LIA: closing connection')

    def flush(self):
        print('DEMO LIA: flushing serial comms')

    def standard_setup(self):
        print('DEMO LIA: Setting up the standard parameters')



class SR530:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        if baudrate < 0:
            self.demomode=True
        else:
            self.demomode=False

        #self.ser = self.connect()
        sleep(0.25)


    def connect(self):
        self.ser = serial.Serial(self.port, self.baudrate, timeout = 0.03)

    def close(self):
        self.ser.close()

    def flush(self):
        self.ser.flush()

    def send(self, input_string):
        output_string = input_string+'\r'
        #print(output_string.encode())
        self.ser.write(output_string.encode())

    def receive_float(self):
        Nrec = self.ser.read(11)
        # Some error handling is necessary. Mainly when it fails due to changes in the LIA filter parameters.
        try:
            output_value = float(Nrec.decode())
        except ValueError:
            print('Error occured in the float decode')
            output_value = 0.0
            # To flush the buffer, I wait and read, twice.
            print('A:'+str(self.ser.readline()))
            sleep(0.1)
            print('Caught error in float reception')
        return output_value

    def measure(self):
        self.send('QX')
        X = self.receive_float()
        self.send('QY')
        Y = self.receive_float()
        return X,Y


    def set_tc(self, tc):
        TcList = ['T 1,1', #1  ms
                  'T 1,2', #3  ms
                  'T 1,3', #10 ms
                  'T 1,4', #30 ms
                  'T 1,5', #100ms
                  'T 1,6', #300ms
                  'T 1,7', #1   s
                  'T 1,8', #3   s
                  'T 1,9', #10  s
                  'T 1,10',#30  s
                  'T 1,11']#100 s
        self.send(TcList[tc])

    def set_sens(self, sens):
                            # Max scale
        sensList = ['G 4',  # 100 nV
                    'G 5',  # 200 nV
                    'G 6',  # 500 nV
                    'G 7',  # 1   uV
                    'G 8',  # 2   uV
                    'G 9',  # 5   uV
                    'G 10', # 10  uV
                    'G 11', # 20  uV
                    'G 12', # 50  uV
                    'G 13', # 100 uV
                    'G 14', # 200 uV
                    'G 15', # 500 uV
                    'G 16', # 1   mV
                    'G 17', # 2   mV
                    'G 18', # 5   mV
                    'G 19', # 10  mV
                    'G 20', # 20  mV
                    'G 21', # 50  mV
                    'G 22', # 100 mV
                    'G 23', # 200 mV
                    'G 24'] # 500 mV
        self.send(sensList[sens])

    def query(self, query):
        self.send(query)
        output = self.ser.readlines()
        return output

    def check_status_byte(self):
        q = self.query('Y')
        b = str(bin(int(q[0])))
        print(b)
        all_ok = True
        status_bits = ['SB 0: Not used',
                       'SB 1: Command parameter out of range',
                       'SB 2: No reference detected',
                       'SB 3: No phase lock',
                       'SB 4: Signal overload',
                       'SB 5: Auto offset out of range',
                       'SB 6: GPIB SRQ',
                       'SB 7: Illegal command string error']
        #zeropad the binary string with 0s to get an 8 bit string:
        byte = '0'*(8-len(b)+2)+b.split('b')[1]
        for n, bit in enumerate(reversed(byte)):
            if bit == '1':
                all_ok = False
                print(status_bits[n])

        if all_ok == True:
            print('All ok')

        return byte

    def standard_setup(self):
        # Set the character waiting time to 0:
        self.send('W0')
        # Set the band pass filter in
        self.send('B1')
        # Set the post filter to 0.1s
        self.send('T2,1')
        # Disengage both line notch filters.
        self.send('L1,0')
        self.send('L2,0')

class ArduinoStageControllerDemo():
    def __init__(self, port, baudrate):
        print('DEMO stage controller instantiating')

    def connect(self):
        print('DEMO stagecontroller connecting')

    def initialize(self):
        print('DEMO stagecontroller initialising and homing')

    def move(self, pos):
        print('DEMO stagecontroller is ordered to move to '+str(pos))

    def close(self):
        pass

    def wait_for_done(self):
        sleep(0.1)

    def read_string(self):
        return 'string'


class ArduinoStageController():

    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate

    def connect(self):
        self.ser = serial.Serial(self.port, self.baudrate, timeout = 0.1)
        sleep(1)

        #run down the buffers initially
        self.ser.write(b'query \r\n')
        garbage = self.read_string()

        self.ser.write(b'query \r\n')
        output = self.read_string()

        if output == 'alive\r\n':
            print('Found arduino on port '+self.port)
        else:
            print('Arduino not found.')

    def initialize(self):
        self.ser.flush()
        self.ser.write(b'init \r\n')    # Find ud af hvorfor der ikke er endelser paa i Peters udgave.
        self.wait_for_done()

    def move(self, x):
        self.ser.write(b'go '+str(int(x)).encode()+'\r\n'.encode())
        #print('move ordered')
        self.wait_for_done()

    def close(self):
        self.ser.close()

    def wait_for_done(self):
        DONE_FOUND_FLAG = False
        while not DONE_FOUND_FLAG:
            string = ""
            bytes_returned = 1
            while bytes_returned > 0:
                read_char = self.ser.read().decode()
                bytes_returned = len(read_char)
                string += read_char

            if 'done' in string:
                DONE_FOUND_FLAG = True

            sleep(0.1)


    def read_string(self):
        string = ""
        bytes_returned = 1
        while bytes_returned > 0:
            read_char = self.ser.read()
            bytes_returned = len(read_char)
            string += read_char.decode()
        #print('read_string function: '+string)

        return string


class log_and_print:
    pass
