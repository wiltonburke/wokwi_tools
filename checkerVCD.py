'''

Example run from command line

python3 checkerVCD.py {design}_logic_analyzer_inputs_0.vcd {design}_logic_analyzer_outputs_0.vcd

Note: It is expecting that {design}.logic.json is available for comparision


Example use from another python script

import checkerVCD

cvcd = checkerVCD()
d1 = cvcd.loadVCD(fileinputs)
d2 = cvcd.loadVCD(fileoutputs)

cvcd.parseVCD(d1, d2, stepSize)

cvcd.checkData(data, truths)

TODO: When wokwi supports multiple Logic Analyzer dumps to a single file will reduce to a single data struct.
 Make it easier to march through time and report the values at those times.

 Copyright (c) burkew, 2022
 wokwi-tools is licensed under the GNU General Public License v3.0
 Copyright and license notices must be preserved. Contributors provide an express grant of patent rights.
'''
import json
import sys
from pyDigitalWaveTools.vcd.parser import VcdParser
from bitstring import BitArray

class checkerVCD():
    def loadVCD(self, filename):
        print("Reading VCD file ", filename)
        
        try:
            with open(filename) as vcd_file:
                vcd = VcdParser()
                vcd.parse(vcd_file)
                dataIn = vcd.scope.toJson()
        except FileNotFoundError:
            print(f"logic file '{filename}' cannot be found.")
            exit(1)
        return dataIn

    def signalsVCD(self, data):
        print("Return list of all the signals in the tv")
        signals = []
        for x in range(len(data['children'])):
            for y in range(len(data['children'][x]['children'])):
                if 'name' in data['children'][x]['children'][y]:
                    signals.append((data['children'][x]['children'][y]['name'], (data['name'],x,y)))
        return signals


    def parseVCD(self, d1, d2, timestep, maxSteps=500,signalList=[]):
        if not signalList:
            signalList = self.signalsVCD(d1)
            signalList = signalList + self.signalsVCD(d2)
        print(" ".join([x[0] for x in signalList]))
        time = 0;
        # add a time index to the datastructure
        for sig in signalList:
            sigName = sig[0]
            sigDataBase = sig[1][0]
            sigX = sig[1][1]
            sigY = sig[1][2]
            if sigDataBase == 'inputs':
                #list0 = d1['children'][sigX]['children'][sigY]['data']
                d1['children'][sigX]['children'][sigY]['index'] = 0
            else:
                d2['children'][sigX]['children'][sigY]['index'] = 0
        maxIndex = 0
        data = []
        while maxIndex < maxSteps:
            newValues = [time]
            for sig in signalList:
                
                sigDataBase = sig[1][0]
                sigX = sig[1][1]
                sigY = sig[1][2]
                
                if sigDataBase == 'inputs':
                    llist0 = d1['children'][sigX]['children'][sigY]['data']
                    llist0index = d1['children'][sigX]['children'][sigY]['index'] 
                else:
                    llist0 = d2['children'][sigX]['children'][sigY]['data']
                    llist0index = d2['children'][sigX]['children'][sigY]['index'] 

                #llist0time = llist0[llist0index][0]
                if llist0index > 0:
                    llist0value = llist0[llist0index-1][1]
                else:
                    llist0value = llist0[llist0index][1]
                #llist0index = llist0index + 1
                while llist0[llist0index][0] <= time:
                    llist0time = llist0[llist0index][0]
                    llist0value = llist0[llist0index][1]
                    llist0index = llist0index + 1
                    if llist0index > maxIndex:
                        maxIndex = llist0index

                newValues.append(llist0value)
                # update the list index ptr
                if sigDataBase == 'inputs':
                    #llist0 = d1['children'][sigX]['children'][sigY]['data']
                    d1['children'][sigX]['children'][sigY]['index'] = llist0index
                else:
                    #llist0 = d2['children'][sigX]['children'][sigY]['data']
                    d2['children'][sigX]['children'][sigY]['index'] = llist0index
            time = time + timestep
            print(" ".join([str(newValues[0])+":"]+newValues[1:]))
            data.append(newValues)
        return data 

    def checkData(self, data, truths, stopVector=None):
        # Check that the truths data specified aligns with the signals captured
        # TODO: expand this to include a settling time/sampling time
        # TODO: expand this to only check n times and not on the full set of data
        # TODO: map pins 
        numInputs = len(truths['inputs'])
        numOutputs = len(truths['outputs'])
        numErrors = 0
        numSamples = 0
        errors = []
        for line in data:
            print(line)
            numSamples = numSamples + 1

            # !! assuming inputs are first in the data set and that the outputs are ordered 
            time = line[0]
            inputVector =line[1:numInputs+1]
            outputVector=line[numInputs+1:]
            indx = BitArray(bin="".join(inputVector)).int
            outputNum = 0 

            # break point to stop at a specific case
            if stopVector:
                if "".join(inputVector) ==stopVector:
                    print(inputVector)

            for key in truths['outputs']:
                testVal = truths['outputs'][key][indx]
                if int(testVal) != int(outputVector[outputNum]):
                    numErrors = numErrors + 1
                    if "".join(inputVector) not in errors:
                        errors["".join(inputVector)] = "".join(["CASE FAILED: ", key, inputVector, 'expected ', testVal, "got ", outputVector[outputNum] ])
                    print("CASE FAILED: ", key, inputVector, 'expected ', testVal, "got ", outputVector[outputNum] )
                else:
                    print("CASE PASSED: ", key, inputVector, 'expected ', testVal, "got ", outputVector[outputNum] )
                outputNum = outputNum + 1
                
            # break point to stop at a specific case
            if stopVector:
                if "".join(inputVector) ==stopVector:
                    print("Stopping at first occurance of ", inputVector)

        print("Number of passing samples ", numSamples - numErrors, " of ", numSamples, " Samples")
        for key in errors:
            print ("".join(errors[key]))


if __name__ == "__main__":
    if len(sys.argv) > 2:
        fnameInputs = sys.argv[1]
        fnameOutputs = sys.argv[2]
    else:
        print('Give me a vcd file to parse')
        sys.exit(-1)
    if len(sys.argv) > 3:
        truthsfilename = sys.argv[3]

    cvcd = checkerVCD()
    dataIn = cvcd.loadVCD(fnameInputs) 
    dataOut = cvcd.loadVCD(fnameOutputs)
    dataIn['name'] = 'inputs'
    dataOut['name'] = 'outputs'
    
    stepSize = 25000
    timeData = cvcd.parseVCD(dataIn, dataOut, stepSize)

    if 'truthsfilename' not in locals():
        truthsfilename = fnameInputs.split('_logic')[0] + '.logic.json'
    try:
        f = open(truthsfilename)
    except FileNotFoundError:
        print(f"logic file '{truthsfilename}' cannot be found.")
        exit(1)

    truths = json.load(f)

    cvcd.checkData(timeData, truths)