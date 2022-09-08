# wokwi_tools
## wokwi tools

## checkerVCD 

   Compare waveform data saved as VCD against a truthtable in a logic.json format.
   For details on the logic.json format look at the lookup table generator found here https://github.com/maehw/wokwi-lookup-table-generator
   The checker is for comparing data that has no registers or state dependacy, such as a lookup table or LUT.
   
   Usage: 
   ```
   python3 checkerVCD examples/limited-ascii_7segment_lut_logic_analyzer_inputs_0.vcd examples/limited-ascii_7segment_lut_logic_analyzer_inputs_0.vcd [truthtable.logic.json]
   ```
   The truthtable must exist, but the name is assumed to be named {design}.logic.json and the design name is extracted from the provided vcd file names.
   The truthtable file name can be provided as a third argument if needed.
   
 ## layoutDiagram
 
   Regenerate the wokwi parts attempting to clean up the layout of large wokwi designs. It is an itial prototype and does not address wiring.
   
   Usage:
   ```
   python3 layoutDiagram.py -f diagram.json -o diagram_layout.json
   ```
 
 
