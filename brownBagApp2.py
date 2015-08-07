#!/usr/bin/python

"""
Copyright (c) 2015

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
 - Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
-  Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
-  Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES;LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

@authors: Sergei Garbuzov

"""

import time
import json


from pybvc.controller.controller import Controller
from pybvc.openflowdev.ofswitch import OFSwitch
from pybvc.openflowdev.ofswitch import FlowEntry
from pybvc.openflowdev.ofswitch import Instruction
from pybvc.openflowdev.ofswitch import OutputAction
from pybvc.openflowdev.ofswitch import Match

from pybvc.common.status import STATUS
from pybvc.common.utils import load_dict_from_file
from pybvc.common.constants import *
from time import gmtime,mktime
from flask import Flask, session, redirect, url_for, escape, request, flash, render_template

app = Flask(__name__)
app.secret_key = 'SomeSecret'


@app.route('/')
def show_entries():
    entries = []
    return render_template('show_entries.html', entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():
    origApp(request.form['srcIp'], request.form['destIp'])
    flash('New flow was successfully created')
    return redirect(url_for('show_entries'))


def origApp(srcIp, destIp):  
    f = "cfg.yml"
    d = {}
    if(load_dict_from_file(f, d) == False):
        print("Config file '%s' read error: " % f)
        exit()
    
    try:
        ctrlIpAddr = d['ctrlIpAddr']
        ctrlPortNum = d['ctrlPortNum']
        ctrlUname = d['ctrlUname']
        ctrlPswd = d['ctrlPswd']
        nodeName = d['nodeName']
    except:
        print ("Failed to get Controller device attributes")
        exit(0)
    
    print ("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    print ("<<< Demo Start")
    print ("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    
    rundelay = 0
    
    ctrl = Controller(ctrlIpAddr, ctrlPortNum, ctrlUname, ctrlPswd)

    
    result = ctrl.get_openflow_nodes_operational_list()
    status = result.get_status()
    if(status.eq(STATUS.OK) == True):
        print ("OpenFlow node names (composed as \"openflow:datapathid\"):")
        nodenames = result.get_data()
        print json.dumps(nodenames, indent=4)
    else:
        print ("\n")
        print ("!!!Demo terminated, reason: %s" % status.brief().lower())
        exit(0)


    idx = mktime(gmtime(0))

    for n in nodenames:
        ofswitch = OFSwitch(ctrl, n)
        
        # --- Flow Match: 
        #                 IPv4 Source Address
        #                 IPv4 Destination Address
        #     NOTE: Ethernet type MUST be 2048 (0x800) -> IPv4 protocol
        eth_type = ETH_TYPE_IPv4
        ipv4_src = srcIp 
        ipv4_dst = destIp
        
        
        print ("<<< 'Controller': %s, 'OpenFlow' switch: '%s'" % (ctrlIpAddr, n))
        
        print "\n"
        print ("<<< Set OpenFlow flow on the Controller")
        print ("        Match:  Ethernet Type (%s)\n"
               "                IPv4 Source Address (%s)\n"
               "                IPv4 Destination Address (%s)\n" % (hex(eth_type), 
                                                                   ipv4_src, ipv4_dst,
                                                                  ))
        print ("        Action: Output (NORMAL)")
        
        
        time.sleep(rundelay)
        
        
    	for i in range(0,2):

            flow_entry = FlowEntry()
            table_id = 0
            flow_entry.set_flow_table_id(table_id)
            flow_id = 16 + idx 
            idx = idx + 1
            flow_entry.set_flow_id(flow_id)
            flow_entry.set_flow_priority(flow_priority = 1007)
            
            # --- Instruction: 'Apply-actions'
            #     Action:      'Output' NORMAL
            instruction = Instruction(instruction_order = 0)
            action = OutputAction(order = 0, port = "NORMAL")
            instruction.add_apply_action(action)
            flow_entry.add_instruction(instruction)
            
            # --- Match Fields: Ethernet Type
            #                   Ethernet Source Address
            #                   Ethernet Destination Address
            #                   IPv4 Source Address
            #                   IPv4 Destination Address
            #                   IP Protocol Number
            #                   IP DSCP
            #                   IP ECN
            #                   TCP Source Port Number
            #                   TCP Destination Port Number
            #                   Input Port
            match = Match()
            match.set_eth_type(eth_type)
            if (i==0):
                match.set_ipv4_src(ipv4_src)
                match.set_ipv4_dst(ipv4_dst)
            else:
                match.set_ipv4_src(ipv4_dst)
                match.set_ipv4_dst(ipv4_src)
                
            flow_entry.add_match(match)
            
            
            print ("\n")
            print ("<<< Flow to send:")
            print flow_entry.get_payload()
            time.sleep(rundelay)
            result = ofswitch.add_modify_flow(flow_entry)
            status = result.get_status()
            if(status.eq(STATUS.OK) == True):
                print ("<<< Flow successfully added to the Controller")
            else:
                print ("\n")
                print ("!!!Demo terminated, reason: %s" % status.brief().lower())
                exit(0)
            
            
            print ("\n")
            print ("<<< Get configured flow from the Controller")
            time.sleep(rundelay)
            result = ofswitch.get_configured_flow(table_id, flow_id)
            status = result.get_status()
            if(status.eq(STATUS.OK) == True):
                print ("<<< Flow successfully read from the Controller")
                print ("Flow info:")
                flow = result.get_data()
                print json.dumps(flow, indent=4)
            else:
                print ("\n")
                print ("!!!Demo terminated, reason: %s" % status.brief().lower())
                exit(0)
        
        
    print ("\n")
    print (">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    print (">>> Demo End")
    print (">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    

if __name__ == '__main__':
    app.run(debug=True)
