#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uniset2.UniXML import UniXML
from uniset2.pyUExceptions import UException
import uniset2.UGlobal as uglobal
import subprocess
import re
from UTestInterface import *
from TestSuiteGlobal import *

'''
Пример файла конфигурации

<?xml version='1.0' encoding='utf-8'?>
<SNMP>
  <Nodes defaultProtocolVersion="2c" defaultTimeout='1' defaultRetries='2'>
    <item name="node1" ip="192.94.214.205" comment="UPS1" protocolVersion="2" timeout='1' retries='2'/>
    <item name="node2" ip="test.net-snmp.org" comment="UPS2"/>
    <item name="ups3" ip="demo.snmplabs.com" comment="DDD"/>
  </Nodes>

  <Parameters defaultReadCommunity="demopublic" defaultWriteCommunity="demoprivate">
    <item name="uptime" OID=".1.3.6.1.2.1.1.3.0" r_community="demopublic"/>
	<item name="uptimeName" community="demopublic" ObjectName="sysUpTime.0"/>
    <item name="sysServ" ObjectName="sysServices.0" r_community="public"/>
	<item name="sysName" ObjectName="sysName.0" w_community="demoprivate" r_community="demopublic"/>
	<item name="sysServ2" ObjectName="sysServices.0" w_community="demoprivate"/>
  </Parameters>
</SNMP>
'''


class UTestInterfaceSNMP(UTestInterface):
    def __init__(self, **kwargs):

        UTestInterface.__init__(self, uts_plugin_name(), **kwargs)

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

        # разбор ответа
        self.replycheck = re.compile(r'^(.*): (.*)$')
        self.re_timeticks = re.compile(r'^\((\d{1,})\)')

        self.snmpget_errors_text = [''
                                    'No Such Instance currently exists at this OID',
                                    'Timeout: No Response from',
                                    ]

        self.snmpset_errors_text = [''
                                    'Unknown Object Identifier',
                                    'Reason: noAccess',
                                    'Error',
                                    'Timeout',
                                    'Bad variable type'
                                    ]

    def initFromFile(self, xmlfile):

        xml = UniXML(xmlfile)
        self.init_nodes(xml)
        self.init_parameters(xml)

    def get_conf_filename(self):
        return self.confile

    @staticmethod
    def get_int_prop(node, propname, defval):
        s = node.prop(propname)
        if s:
            return uglobal.to_int(s)

        return defval

    @staticmethod
    def get_prop(node, propname, defval):
        s = node.prop(propname)
        if s:
            return s

        return defval

    @staticmethod
    def get_prot_version(protocolVersion, defval='2'):

        if protocolVersion == '1':  # SNMPv1
            return '1'

        if protocolVersion == '2' or protocolVersion == '2c':  # SNMPv2c
            return '2c'

        return defval

    def init_nodes(self, xml):

        node = xml.findNode(xml.getDoc(), "Nodes")[0]
        if node is None:
            raise TestSuiteValidateError("(snmp): section <Nodes> not found in %s" % xml.getFileName())

        defaultProtocolVersion = self.get_prop(node, "defaultProtocolVersion", '2c')
        defaultTimeout = self.get_int_prop(node, "defaultTimeout", 1)
        defaultRetries = self.get_int_prop(node, "defaultRetries", 1)
        defaultPort = self.get_int_prop(node, "defaultPort", 161)
        defaultMIBfile = self.get_prop(node, "defaultMIBfile", '')

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

            protocolVersion = self.get_prop(node, "protocolVersion", defaultProtocolVersion)

            item['version'] = self.get_prot_version(protocolVersion)
            item['port'] = self.get_int_prop(node, "port", defaultPort)
            item['timeout'] = self.get_int_prop(node, "timeout", defaultTimeout)
            item['retries'] = self.get_int_prop(node, "retries", defaultRetries)
            item['mibfile'] = self.get_prop(node, "mibfile", defaultMIBfile)

            if item['name'] in self.nodes:
                raise TestSuiteValidateError(
                    "(snmp):  <Parameters> : ERR: node name '%s' ALEREADY EXIST ['%s']" % (
                        item['name'], xml.getFileName()))

            self.nodes[item['name']] = item

            node = xml.nextNode(node)

    def init_parameters(self, xml):

        node = xml.findNode(xml.getDoc(), "Parameters")[0]
        if node is None:
            raise TestSuiteValidateError("(snmp): section <Parameters> not found in %s" % xml.getFileName())

        defaultReadCommunity = uglobal.to_str(node.prop("defaultReadCommunity"))
        defaultWriteCommunity = uglobal.to_str(node.prop("defaultWriteCommunity"))

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

            item['r_community'] = self.get_prop(node, "r_community", defaultReadCommunity)
            item['w_community'] = self.get_prop(node, "w_community", defaultWriteCommunity)

            if item['name'] in self.mibparams:
                raise TestSuiteValidateError(
                    "(snmp):  <Parameters> : ERR: name '%s' ALEREADY EXIST ['%s']" % (
                        item['name'], xml.getFileName()))

            self.mibparams[item['name']] = item

            node = xml.nextNode(node)

    @staticmethod
    def parse_id(name):
        """
        Parse test parameter from <check> or <action>
        :param name:
        :return: [id,node,name]
        """
        vname, vnode = uglobal.get_sinfo(name, '@')
        return [vname, vnode, name]

    def get_parameter(self, name):

        try:
            return self.mibparams[name]
        except (KeyError, ValueError):
            return None

    def get_node(self, name):

        try:
            return self.nodes[name]
        except (KeyError, ValueError):
            return None

    def get_value(self, name):

        ret, err = self.validate_parameter(name)

        if ret == False:
            raise TestSuiteValidateError("(snmp): get_value : ERR: '%s'" % err)

        id, nodename, sname = self.parse_id(name)

        param = self.get_parameter(id)
        node = self.get_node(nodename)

        return self.snmp_get(param, node)

    def snmp_get(self, param, node):

        var_name = None
        if param['OID']:
            var_name = param['OID']
        elif param['ObjectName']:
            var_name = param['ObjectName']
        else:
            raise TestSuiteValidateError("(snmp): get_value : Unknown OID for '%s'" % param['name'])

        s_out = ''
        s_err = ''

        cmd = "snmpget -v %s -c %s -t %d -r %d -O v %s %s" % (
            node['version'],
            param['r_community'],
            uglobal.to_int(node['timeout']),
            uglobal.to_int(node['retries']),
            node['ip'],
            var_name
        )

        try:

            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True, shell=True)
            s_out = p.stdout.read(120)
            s_err = p.stderr.read(120)

        except Exception, e:
            raise TestSuiteValidateError("(snmp): get_value error: %s for %s" % (e.message, var_name))

        if not s_out or len(s_out) == 0:
            raise TestSuiteValidateError("(snmp): get_value error: NO READ DATA for %s" % var_name)

        # поверка ответа на ошибки
        for err in self.snmpget_errors_text:
            if err in s_out:
                raise TestSuiteValidateError("(snmp): get_value error: %s" % s_out.replace("\n", " "))

        for err in self.snmpget_errors_text:
            if err in s_err:
                raise TestSuiteValidateError("(snmp): get_value error: %s" % s_err.replace("\n", " "))

        ret = self.replycheck.findall(s_out)
        if not ret or len(ret) == 0:
            raise TestSuiteValidateError("(snmp): get_value error: BAD REPLY FORMAT: %s" % s_out.replace("\n", " "))

        val = self.parse_value(ret[0])
        if val == None:
            raise TestSuiteValidateError("(snmp): get_value error: UNKNOWN VALUE: %s" % s_out.replace("\n", " "))

        return val

    def parse_value(self, lst):

        vtype = lst[0].upper()
        sval = lst[1]

        if vtype == 'INTEGER':
            return uglobal.to_int(sval)

        if vtype == 'STRING':
            return sval

        if vtype == 'TIMETICKS':
            ret = self.re_timeticks.findall(sval)
            if not ret or len(ret) == 0:
                return None

            lst = ret[0]
            if not lst or len(lst) < 1:
                return None

            return uglobal.to_int(lst[0])

        return None

    def set_value(self, name, value, supplierID):
        ret, err = self.validate_parameter(name)

        if ret == False:
            raise TestSuiteValidateError("(snmp): set_value : ERR: '%s'" % err)

        id, nodename, sname = self.parse_id(name)

        param = self.get_parameter(id)
        node = self.get_node(nodename)

        self.snmp_set(param, node, value)

    def snmp_set(self, param, node, value):

        var_name = None

        #  \todo Пока-что поддерживается только type INTEGER'''
        var_type = "i"

        if param['OID']:
            var_name = param['OID']
        elif param['ObjectName']:
            var_name = param['ObjectName']
        else:
            raise TestSuiteValidateError("(snmp): get_value : Unknown OID for '%s'" % param['name'])

        s_err = ''
        try:
            cmd = "snmpset -v %s -c %s -t %d -r %d %s %s %s %s" % (
                node['version'],
                param['w_community'],
                uglobal.to_int(node['timeout']),
                uglobal.to_int(node['retries']),
                node['ip'],
                var_name, var_type, value)

            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True, shell=True)
            s_err = p.stderr.read(120)

        except Exception, e:
            raise TestSuiteValidateError("(snmp): set_value err: %s for %s" % (e.message, var_name))

        if len(s_err) > 0:
            for err in self.snmpset_errors_text:
                if err in s_err:
                    raise TestSuiteValidateError("(snmp): set_value err: %s" % s_err.replace("\n", " "))

    def ping(self, ip):
        """
        Проверка доступности через запуск ping. Пока-что это самый простой способ
        :param ip: адрес узла
        :return: True - если связь есть
        """
        nul_f = open(os.devnull, 'w')
        cmd = "ping -c 2 -i 0.4 -w 3 %s" % ip
        ret = subprocess.call(cmd, shell=True, stdout=nul_f, stderr=nul_f)
        nul_f.close()

        if ret:
            return False

        return True

    def get_variables_from_mib(self, mibfile):

        if not os.path.isfile(mibfile):
            raise TestSuiteValidateError(
                "(snmp): get_variables_from_mib : ERR: file not found '%s'" % mibfile)

        cmd = "snmptranslate -Tz -m %s" % mibfile
        ret = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        lines = ret.communicate()[0].split('\n')
        rcheck = re.compile(r'^"(.*)"\s{0,}"(.*)"$')
        vars = dict()

        for l in lines:
            ret = rcheck.findall(l)
            if not ret:
                continue

            v = ret[0]
            if len(v) < 2:
                raise TestSuiteValidateError(
                    "(snmp): get_variables_from_mib : ERR: BAD FILE FORMAT for string '%s'" % l)

            vars[v[0]] = v[1]

        return vars

    @staticmethod
    def check_oid(oid, mibs):
        for m in mibs:
            if oid in m:
                return True

        return False

    def validate_configuration(self):
        """
        Проверка конфигурации snmp
        :return: result[] - см. TestSuiteGlobal make_default_item():
        """
        res_ok = True
        errors = []

        # Если отключена проверка узлов, то нам и проверять нечего
        if self.ignore_nodes:
            return [True, '']

        # 1. Проверка доступности узлов
        for k, node in self.nodes.items():
            if not self.ping(node['ip']):
                errors.append("\t(snmp): CONF[%s] ERROR: '%s' not available" % (self.confile, node['ip']))
                res_ok = False

        # Проверка переменных через MIB-файлы
        mibfiles = list()
        for k, node in self.nodes.items():
            if node['mibfile']:
                if node['mibfile'] not in mibfiles:
                    mibfiles.append(node['mibfile'])

        if len(mibfiles) > 0:
            mibs = list()
            for f in mibfiles:
                mibs.append(self.get_variables_from_mib(f))

            # Ищем переменные во всех загруженных словарях..
            for oid, var in self.mibparams.items():
                if not self.check_oid(oid, mibs):
                    errors.append("\t(snmp): CONF[%s] ERROR: NOT FOUND OID '%s' in mibfiles.." % (self.confile, oid))
                    res_ok = False

        err = ''
        if len(errors) > 0:
            err = "(snmp): ERRORS: \n %s" % '\n'.join(errors)

        return [res_ok, err]

    def validate_parameter(self, name):

        try:
            vname, vnode, fname = self.parse_id(name)
            if vname == '':
                return [False, "(snmp): Unknown ID for '%s'" % str(name)]

            param = self.get_parameter(vname)

            if not param:
                return [False, "Unknown OID or ObjectName for '%s'" % str(name)]

            node = self.get_node(vnode)

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
