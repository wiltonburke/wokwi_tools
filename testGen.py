'''

Example run from command line

python3 testGen.py diagram.json



Example use from another python script

import testGen

testgen = testGen(file, [inputs], [outputs])
newdesign = testGen.diagram


def write_design(filename, design):
    with open(ofname, 'w', encoding='utf-8') as f:
        json.dump(design, f, ensure_ascii=False, indent=4)


 Copyright (c) burkew, 2022
 wokwi-tools is licensed under the GNU General Public License v3.0
 Copyright and license notices must be preserved. Contributors provide an express grant of patent rights.
'''
import json
import math

wokwi_part_template = {
    "type": "wokwi-part-template",
    "id": None,
    "top": 0,
    "left": 0,
    "attrs": {}
}
wokwi_part_types = {"la":"wokwi-logic-analyzer", 
                  "clk":"wokwi-clock-generator", 
                  "dff":"wokwi-flip-flop-d"}


class testgen():
    def __init__(self, filename, inputs, outputs):
        self.diagram = None
        self.design_name = "design"
        self.INSERT_LOGIC_ANALYZER = True
        self.INSERT_TEST_VECTOR = True 
        try:
            with open(filename) as f:
                self.diagram = json.load(f)
        except FileNotFoundError:
            print(f"wokwi diagram file '{filename}' cannot be found.")
        self.inputs = inputs
        self.outputs = outputs
    
    def gen(self):
        if self.INSERT_LOGIC_ANALYZER:
            self.insertLogicAnalyzer()
        if self.INSERT_TEST_VECTOR:
            self.insertTestVector()

    def nameInDiagram(self,name):
        return False

    def insertTestVector(self):
        clockname = "testvector_clock" 
        num = 0
        while(self.nameInDiagram(clockname + str(num))):
            num = num + 1
        clockname = clockname + str(num)
        clocknameprev = ""
        con_color = "YELLOW"
        default_con_instr = ["h10", "*", "h-10"]
        for k in range(len(self.inputs)):
            if k == 0:
                # drop a clock source and tie it to the first input
                clockname = "testvector_clock"
                wokwi_clock_generator_inst = wokwi_part_template.copy()
                wokwi_clock_generator_inst['type'] = wokwi_part_types['clk']
                wokwi_clock_generator_inst['id'] = clockname
                wokwi_clock_generator_inst['top'] = -600
                wokwi_clock_generator_inst['left'] = 000
                self.diagram["parts"].append(wokwi_clock_generator_inst)

                con = [ f"{clockname}:CLK", f"{self.inputs[k]}:IN",
                        con_color, default_con_instr ]
                #log.debug("    Connection: "+str(con))
                self.diagram["connections"].append(con)
                clocknameprev = clockname
            else:
                # drop a dff and tie its clock to the last dff/clock source 
                # tie the d input to the q not output
                clockname = "testvector_clock_div"+ str(int(math.pow(2,k)))

                wokwi_flip_flop_d_inst = wokwi_part_template.copy()
                wokwi_flip_flop_d_inst['type'] = wokwi_part_types['dff']
                wokwi_flip_flop_d_inst['id'] = clockname
                wokwi_flip_flop_d_inst['top'] = -600
                wokwi_flip_flop_d_inst['left'] = 200 * k
                self.diagram["parts"].append(wokwi_flip_flop_d_inst)

                pin = 'CLK' if clocknameprev == 'testvector_clock' else 'Q' 
                con = [ f"{clocknameprev}:{pin}", f"{clockname}:CLK",
                        con_color, default_con_instr ]
                #log.debug("    Connection: "+str(con))
                self.diagram["connections"].append(con)

                
                # tie the q output to the input
                con = [ f"{clockname}:Q", f"{self.inputs[k]}:IN",
                        con_color, [f"h{wokwi_flip_flop_d_inst['left']+50}", f"v{wokwi_flip_flop_d_inst['top']}"] ]
                #log.debug("    Connection: "+str(con))
                self.diagram["connections"].append(con)

                con = [ f"{clockname}:NOTQ", f"{clockname}:D",
                        con_color,  ["h29.43", "v-36.17", "h-125.43"]  ]
                #log.debug("    Connection: "+str(con))
                self.diagram["connections"].append(con)

                clocknameprev = clockname

    def insertLogicAnalyzer(self): # add Logic analyzers on inputs and outputs 
        con_color = "YELLOW"
        default_con_instr = ["h10", "*", "h-10"]
        # Dont mix inputs and outputs or it will be harder to match them up for comparision
        for k in range( math.ceil(len(self.inputs)/8)):
            wokwi_logic_analyzer_inst = wokwi_part_template.copy()
            wokwi_logic_analyzer_inst['type'] = wokwi_part_types['la']
            wokwi_logic_analyzer_inst['id'] = "logic_analyzer_inputs_" + str(k)
            wokwi_logic_analyzer_inst['top'] = -200 * (k+1)
            wokwi_logic_analyzer_inst['left'] = 400
            ## Temp to work around bug in wokwi save all logic analyzers to unique file names 
            wokwi_logic_analyzer_inst['attrs'] = {"filename":f"{self.design_name}_logic_analyzer_inputs_" + str(k)}

            self.diagram["parts"].append(wokwi_logic_analyzer_inst)

        for k in range( math.ceil(len(self.outputs)/8)):
            wokwi_logic_analyzer_inst = wokwi_part_template.copy()
            wokwi_logic_analyzer_inst['type'] = wokwi_part_types['la']
            wokwi_logic_analyzer_inst['id'] = "logic_analyzer_outputs_" + str(k)
            wokwi_logic_analyzer_inst['top'] = -200 * (k+1)
            wokwi_logic_analyzer_inst['left'] = 800
            ## Temp to work around bug in wokwi save all logic analyzers to unique file names 
            wokwi_logic_analyzer_inst['attrs'] = {"filename":f"{self.design_name}_logic_analyzer_outputs_" + str(k)}
            self.diagram["parts"].append(wokwi_logic_analyzer_inst)

        # connect previous OR gate's output to current OR gate's input port
        currentAnalyzer = 0
        for k in range(len(self.inputs)):
            con = [ f"{self.inputs[k]}:IN", f"logic_analyzer_inputs_{currentAnalyzer}:D{k}",
                    con_color, default_con_instr ]
            #log.debug("    Connection: "+str(con))
            self.diagram["connections"].append(con)
            if (k+1)%8 == 0:
                currentAnalyzer = currentAnalyzer+1

        currentAnalyzer = 0
        for k in range(len(self.outputs)):
            con = [ f"{self.outputs[k]}:OUT", f"logic_analyzer_outputs_{currentAnalyzer}:D{k}",
                    con_color, default_con_instr ]
            #log.debug("    Connection: "+str(con))
            self.diagram["connections"].append(con)
            if (k+1)%8 == 0:
                currentAnalyzer = currentAnalyzer+1

if __name__ == "__main__":
    inputs = ['input_a', 'input_b', 'input_c', 'input_d', 'input_e']
    outputs = ['output_a', 'output_b', 'output_c', 'output_d', 'output_e', 'output_f', 'output_g' ]
    
    testgen = testgen("examples/7segexample.json", inputs, outputs)
    testgen.design_name = "limited-ascii_7segment_lut"
    testgen.gen()
   
    ofname = "examples/test7segexample.json"
    with open(ofname, 'w', encoding='utf-8') as f:
        json.dump(testgen.diagram, f, ensure_ascii=False, indent=4)