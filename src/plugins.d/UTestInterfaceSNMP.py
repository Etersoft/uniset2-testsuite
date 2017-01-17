#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uniset2.UniXML import UniXML
from uniset2.pyUExceptions import UException
import uniset2.UGlobal as uglobal
import pysnmp
from pysnmp.entity.rfc3413.oneliner import cmdgen as snmp
from UTestInterface import *

'''
Пример файла конфигурации

<?xml version='1.0' encoding='utf-8'?>
<SNMP>
  <Nodes defaultProtocolVersion="2c" defaultTimeout='1' defaultRetries='2' defaultPort='161'>
    <item name="node1" ip="192.94.214.205" comment="UPS1" protocolVersion="1" timeout='1' retries='2'/>
    <item name="node2" ip="test.net-snmp.org" comment="UPS2"/>
    <item name="node3" ip="demo.snmplabs.com" comment="DDD"/
  </Nodes>

  <Parameters defaultCommunity="demopublic">
    <item name="uptime" OID="1.3.6.1.2.1.1.3.0" community="demopublic" ObjectName="SNMPv2-MIB::sysUpTime.0"/>
    <item name="bstatus" OID="1.3.6.1.2.1.33.1.2.1.0" ObjectName="BatteryStatus"/>
    <item name="btime" OID=".1.3.6.1.2.1.33.1.2.2.0" ObjectName="TimeOnBattery"/>
    <item name="bcharge" OID=".1.3.6.1.2.1.33.1.2.4.0" ObjectName="BatteryCharge"/>
    <item name="sysServ" ObjectName="sysServices.0" community="public"/>
  </Parameters>
</SNMP>
'''


class UTestInterfaceSNMP(UTestInterface):
    def __init__(self, **kwargs):

        UTestInterface.__init__(self, "snmp", **kwargs)

        snmpConFile = None

        # конфигурирование из xmlnode
        if 'xmlConfNode' in kwargs:
            xmlConfNode = kwargs['xmlConfNode']
            if not xmlConfNode:
                raise TestSuiteValidateError("(snmp:init): Unknown confnode")
            snmpConFile = uglobal.to_str(xmlConfNode.prop("snmp"))
            if not snmpConFile:
                raise TestSuiteValidateError("(snmp:init): Not found snmp='' in %s" % str(xmlConfNode))

        # конфигурирование прямым указанием файла
        elif 'snmpConFile' in kwargs:
            snmpConFile = kwargs['snmpConFile']

        if not snmpConFile:
            raise TestSuiteValidateError("(snmp:init): Unknown snmp configuration file")

        self.mibparams = dict()
        self.nodes = dict()
        self.confile = snmpConFile

        self.initFromFile(snmpConFile)

        self.snmp = snmp.CommandGenerator()

    def initFromFile(self, xmlfile):

        xml = UniXML(xmlfile)
        self.initNodesList(xml)
        self.initParameters(xml)

    def getConfFileName(self):
        return self.confile

    @staticmethod
    def getIntProp(node, propname, defval):
        s = node.prop(propname)
        if s:
            return uglobal.to_int(s)

        return defval

    @staticmethod
    def getProp(node, propname, defval):
        s = node.prop(propname)
        if s:
            return s

        return defval

    @staticmethod
    def getMPModel(protocolVersion, defval=1):

        # преобразуем версию в число для pysnmp
        # см. http://pysnmp.sourceforge.net/docs/pysnmp-hlapi-tutorial.html#choosing-snmp-protocol-and-credentials

        if protocolVersion == '1':  # SNMPv1
            return 0

        if protocolVersion == '2' or protocolVersion == '2c':  # SNMPv2c
            return 1

        return defval

    def initNodesList(self, xml):

        node = xml.findNode(xml.getDoc(), "Nodes")[0]
        if node is None:
            raise TestSuiteValidateError("(snmp): section <Nodes> not found in %s" % xml.getFileName())

        defaultProtocolVersion = self.getProp(node, "defaultProtocolVersion", '2c')
        defaultTimeout = self.getIntProp(node, "defaultTimeout", 1)
        defaultRetries = self.getIntProp(node, "defaultRetries", 1)
        defaultPort = self.getIntProp(node, "defaultPort", 161)

        # elif defaultProtocolVersion == 3:
        #     defaultPass =
        #     defaultLogin =

        node = xml.firstNode(node.children)

        while node is not None:

            item = dict()

            item['name'] = uglobal.to_str(node.prop("name"))
            if item['name'] == "":
                raise TestSuiteValidateError(
                    "(snmp): <Nodes> : unknown name='' for string '%s' in file %s" % (
                        str(node), xml.getFileName()))

            item['ip'] = uglobal.to_str(node.prop("ip"))
            if item['ip'] == "":
                raise TestSuiteValidateError(
                    "(snmp): <Nodes> : unknown ip='' for string '%s' in file %s" % (
                        str(node), xml.getFileName()))

            item['comment'] = uglobal.to_str(node.prop("comment"))

            protocolVersion = self.getProp(node, "protocolVersion", defaultProtocolVersion)

            item['mpModel'] = self.getMPModel(protocolVersion)
            item['port'] = self.getIntProp(node, "port", defaultPort)
            item['timeout'] = self.getIntProp(node, "timeout", defaultTimeout)
            item['retries'] = self.getIntProp(node, "retries", defaultRetries)

            self.nodes[item['name']] = item

            node = xml.nextNode(node)

    def initParameters(self, xml):

        node = xml.findNode(xml.getDoc(), "Parameters")[0]
        if node is None:
            raise TestSuiteValidateError("(snmp): section <Parameters> not found in %s" % xml.getFileName())

        defaultCommunity = uglobal.to_str(node.prop("defaultCommunity"))

        node = xml.firstNode(node.children)

        while node is not None:

            item = dict()

            item['name'] = uglobal.to_str(node.prop("name"))
            if item['name'] == "":
                raise TestSuiteValidateError(
                    "(snmp): <Parameters> : unknown name='' for string '%s' in file %s" % (
                        str(node), xml.getFileName()))

            item['ObjectName'] = uglobal.to_str(node.prop("ObjectName"))
            item['OID'] = uglobal.to_str(node.prop("OID"))

            if not item['OID'] and not item['ObjectName']:
                raise TestSuiteValidateError(
                    "(snmp):  <Parameters> : unknown OID='' or ObjectName='' for parameter '%s' in file %s" % (
                        str(node), xml.getFileName()))

            item['community'] = self.getProp(node, "community", defaultCommunity)

            self.mibparams[item['name']] = item

            node = xml.nextNode(node)

    @staticmethod
    def parseID(name):
        """
        Parse test parameter from <check> or <action>
        :param name:
        :return: [id,node,name]
        """
        vname, vnode = uglobal.get_sinfo(name, '@')
        return [vname, vnode, name]

    def getParameter(self, name):

        try:
            return self.mibparams[name]
        except KeyError, e:
            return None
        except ValueError, e:
            return None

    def getNode(self, name):

        try:
            return self.nodes[name]
        except KeyError:
            return None
        except ValueError:
            return None

    def getValue(self, name):

        try:

            ret, err = self.validateParameter(name)

            if ret == False:
                raise TestSuiteValidateError("(snmp): 'getValue' ERR: '%s'" % err)

            id, nodename, sname = self.parseID(name)

            param = self.getParameter(id)
            node = self.getNode(nodename)

            varName = None

            if param['OID']:
                varName = snmp.MibVariable(param['OID'])
            elif param['ObjectName']:

                # Парсим строку вида: SNMPv2-MIB::sysUpTime.0
                # при этом этой части 'SNMPv2-MIB' может быть не задано
                tmp = param['ObjectName']
                v = tmp.split('::')
                pname = ''
                if len(v) > 1:
                    pname = v[0]
                    tmp = v[1]

                v = tmp.split('.')
                vname = v[0]
                vnum = 0
                if len(v) > 1:
                    vnum = uglobal.to_int(v[1])

                varName = snmp.MibVariable(pname, vname, vnum)
            else:
                raise TestSuiteValidateError("(snmp): 'getValue' Unknown OID for '%s'" % name)

            community = snmp.CommunityData(param['community'], mpModel=node['mpModel'])
            transport = snmp.UdpTransportTarget((node['ip'], node['port']), timeout=node['timeout'],
                                                retries=node['retries'])

            errorIndication, errorStatus, errorIndex, varBinds = self.snmp.getCmd(
                community,
                transport,
                varName
            )

            if errorIndication:
                raise TestSuiteValidateError("(snmp): getValue : ERR: %s" % errorIndication)

            if errorStatus:
                raise TestSuiteValidateError("(snmp): getValue : ERR: %s at %s " % (
                    errorStatus.prettyPrint(), errorIndex and varBinds[int(errorIndex) - 1] or '?'))

            if len(varBinds) <= 0:
                raise TestSuiteValidateError("(snmp): getValue : ERR: NO DATA?!!")

            varname, val = varBinds[0]
            return val

        except UException, e:
            raise e

    def setValue(self, name, value, supplierID):

        ret, err = self.validateParameter(name)

        if ret == False:
            raise TestSuiteValidateError("(snmp): 'setValue' ERR: '%s'" % err)

        # todo Реализовать функцию setValue
        raise TestSuiteException("(snmp): 'setValue' function not supported)")

    def validateConfiguration(self):
        # todo Реализовать функцию проверки конфигурации
        return [True, ""]

    def validateParameter(self, name):

        try:
            vname, vnode, fname = self.parseID(name)
            if vname == '':
                return [False, "(snmp): Unknown ID for '%s'" % str(name)]

            param = self.getParameter(vname)

            if not param:
                return [False, "Unknown OID or ObjectName for '%s'" % str(name)]

            node = self.getNode(vnode)

            if not node:
                return [False, "(snmp): Unknown node ('%s') for '%s'" % (vnode, str(name))]

            return [True, ""]

        except UException, e:
            return [False, "%s" % e.getError()]


def uts_create_from_args(**kwargs):
    """
    Создание интерфейса
    :param kwargs: именованные параметры
    :return: объект наследник UTestInterface
    """
    return UTestInterfaceSNMP(**kwargs)


def uts_create_from_xml(xmlConfNode):
    """
    Создание интерфейса
    :param xmlConfNode: xml-узел с настройками
    :return: объект наследник UTestInterface
    """
    return UTestInterfaceSNMP(xmlConfNode=xmlConfNode)


def uts_plugin_name():
    return "snmp"
