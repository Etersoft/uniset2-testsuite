#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uniset2.UInterface import *
from uniset2.UGlobal import *
from uniset2.UniXML import *
from uniset2.pyUExceptions import *
import netsnmp

'''
Пример файла конфигурации

<?xml version='1.0' encoding='utf-8'?>
<SNMP>
<Nodes>
     <item name="node1" ip="10.16.11.1" comment="UPS1"/>
     <item name="node2" ip="10.16.11.2" comment="UPS2"/>
     <item name="node3" ip="10.16.11.3" comment="UPS3"/>
</Nodes>
<Parameters>
	<item name="status" OID="1.3.6.1.2.1.33.1.2.1.0" ObjectName="BatteryStatus"/>
	<item name="voltage" OID="1.3.6.1.2.1.33.1.2.1.0" ObjectName="BatteryVoltage"/>
</Parameters>
</SNMP>
'''


class UInterfaceSNMP(UInterface):
    def __init__(self, snmpConfile):
        UInterface.__init__(self)

        self.itype = "snmp"
        self.i = None
        self.mibparams = dict()
        self.nodes = dict()
        self.confile = snmpConfile

        self.initFromFile(snmpConfile)

    def initFromFile(self, xmlfile):

        xml = UniXML(xmlfile)
        self.initNodesList(xml)
        self.initParameters(xml)

    def initNodesList(self, xml):

        node = xml.findNode(xml.getDoc(), "Nodes")[0]
        if node is None:
            raise UValidateError("(UInterfaceSNMP): section <Nodes> not found in %s" % xml.getFileName())

        node = xml.firstNode(node.children)

        while node is not None:

            item = dict()

            item['name'] = to_str(node.prop("name"))
            if item['name'] == "":
                raise UValidateError(
                    "(UInterfaceSNMP): <Nodes> : unknown name='' for string '%s' in file %s" % (
                        str(node), xml.getFileName()))

            item['ip'] = to_str(node.prop("ip"))
            if item['ip'] == "":
                raise UValidateError(
                    "(UInterfaceSNMP): <Nodes> : unknown ip='' for string '%s' in file %s" % (
                        str(node), xml.getFileName()))

            item['comment'] = to_str(node.prop("comment"))

            self.nodes[item['name']] = item

            node = xml.nextNode(node)

    def initParameters(self, xml):

        node = xml.findNode(xml.getDoc(), "Parameters")[0]
        if node is None:
            raise UValidateError("(UInterfaceSNMP): section <Parameters> not found in %s" % xml.getFileName())

        node = xml.firstNode(node.children)

        while node is not None:

            item = dict()

            item['name'] = to_str(node.prop("name"))
            if item['name'] == "":
                raise UValidateError(
                    "(UInterfaceSNMP): <Parameters> : unknown name='' for string '%s' in file %s" % (
                        str(node), xml.getFileName()))

            item['OID'] = to_str(node.prop("OID"))
            if item['OID'] == "":
                raise UValidateError(
                    "(UInterfaceSNMP):  <Parameters> : unknown OID='' for string '%s' in file %s" % (
                        str(node), xml.getFileName()))

            item['ObjectName'] = to_str(node.prop("ObjectName"))

            self.mibparams[item['name']] = item

            node = xml.nextNode(node)

    # return [id,node,name]
    def getIDinfo(self, name):
        id, node = get_sinfo(name, '@')
        return [id, node, name]

    def getParam(self, name):

        try:
            return self.mibparams[name]
        except KeyError, e:
            return None
        except ValueError, e:
            return None

    def getNode(self, name):

        try:
            return self.nodes[name]
        except KeyError, e:
            return None
        except ValueError, e:
            return None

    # return [ RESULT, ERROR ]
    def validateParam(self, name):

        try:
            id, node, fname = self.getIDinfo(name)
            if id == '':
                return [False, "Unknown ID for '%s'" % str(name)]

            return [True, ""]

        except UException, e:
            return [False, "%s" % e.getError()]

    def getValue(self, name):

        try:
            id, nodename, sname = self.getIDinfo(name)

            param = self.getParam(id)
            node = self.getNode(nodename)
            # print "(GETVALUE): param=%s   node=%s"%(str(param),str(node))
            return 0

        except UException, e:
            raise e

    def setValue(self, name, val, supplier=DefaultSupplerID):
        raise UValidateError("(UInterfaceSNMP): 'setValue' function not supported)")

    def getConfFileName(self):
        return self.confile

    def getShortName(self, s_node):
        return ''

    def getNodeID(self, s_node):
        return None

    def getSensorID(self, s_name):
        return None

    def getObjectID(self, o_name):
        return None
