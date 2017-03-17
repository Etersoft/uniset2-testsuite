#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uniset2.UniXML import UniXML
from uniset2.pyUExceptions import UException
import uniset2.UGlobal as uglobal
import subprocess
import re
import glob
import os
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
  <MIBdirs>
	  <dir path="conf/" mask="*.mib"/>
	  <dir path="conf2/" mask="*.mib"/>
  </MIBdirs>
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
        self.mibdirs = list()
        self.confile = snmpConFile
        self.init_from_file(snmpConFile)

        # разбор ответа
        self.replycheck = re.compile(r'^(.*): (.*)$')
        self.re_timeticks = re.compile(r'^\((\d{1,})\)')

        self.snmpget_errors = [''
                               'No Such Instance currently exists at this OID',
                               'Timeout: No Response from',
                               ]

        self.snmpset_errors = [''
                               'Unknown Object Identifier',
                               'Reason: noAccess',
                               'Error',
                               'Timeout',
                               'Bad variable test_type'
                               ]

    def init_from_file(self, xmlfile):

        xml = UniXML(xmlfile)
        self.init_nodes(xml)
        self.init_mibdirs(xml)
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

            if item['name'] in self.nodes:
                raise TestSuiteValidateError(
                    "(snmp):  <Nodes> : ERR: node name '%s' ALEREADY EXIST ['%s']" % (
                        item['name'], xml.getFileName()))

            self.nodes[item['name']] = item

            node = xml.nextNode(node)

    def init_mibdirs(self, xml):

        node = xml.findNode(xml.getDoc(), "MIBdirs")[0]
        if node is None:
            return
            # raise TestSuiteValidateError("(snmp): section <MIBdirs> not found in %s" % xml.getFileName())

        defaultMask = self.get_prop(node, "defaultMask", '')

        node = xml.firstNode(node.children)
        while node is not None:

            item = dict()

            item['path'] = uglobal.to_str(node.prop("path"))
            if item['path'] == "":
                raise TestSuiteValidateError(
                    "(snmp): <MIBdirs> : unknown path='' for string '%s' in file %s" % (
                        str(node), xml.getFileName()))

            item['mask'] = uglobal.to_str(self.get_prop(node, "mask", defaultMask))

            if item['path'] in self.nodes:
                raise TestSuiteValidateError(
                    "(snmp):  <MIBdirs> : ERR: path='%s' ALEREADY EXIST ['%s']" % (
                        item['path'], xml.getFileName()))

            if not os.path.isdir(item['path']):
                raise TestSuiteValidateError(
                    "(snmp):  <MIBdirs> : ERR: path='%s' NOT FOUND ['%s']" % (
                        item['path'], xml.getFileName()))

            self.mibdirs.append(item)

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
            item['ignoreCheckMIB'] = self.get_int_prop(node, "ignoreCheckMIB", 0)

            if item['name'] in self.mibparams:
                raise TestSuiteValidateError(
                    "(snmp):  <Parameters> : ERR: name '%s' ALEREADY EXIST ['%s']" % (
                        item['name'], xml.getFileName()))

            self.mibparams[item['name']] = item

            node = xml.nextNode(node)

    @staticmethod
    def parse_name(name):
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

    def get_value(self, name, context):

        ret, err = self.validate_parameter(name, context)

        if ret == False:
            raise TestSuiteValidateError("(snmp): get_value : ERR: '%s'" % err)

        id, nodename, sname = self.parse_name(name)

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

        # поверка ответа на ошибки
        for err in self.snmpget_errors:
            if err in s_err:
                raise TestSuiteValidateError("(snmp): get_value error: %s" % s_err.replace("\n", " "))

        # поверка ответа на ошибки
        for err in self.snmpget_errors:
            if err in s_out:
                raise TestSuiteValidateError("(snmp): get_value error: %s" % s_out.replace("\n", " "))

        if not s_out or len(s_out) == 0:
            raise TestSuiteValidateError("(snmp): get_value error: NO READ DATA for %s" % var_name)

        ret = self.replycheck.findall(s_out)
        if not ret or len(ret) == 0:
            raise TestSuiteValidateError("(snmp): get_value error: BAD REPLY FORMAT: %s" % s_out.replace("\n", " "))

        val = self.parse_value(ret[0])
        if val == None:
            raise TestSuiteValidateError("(snmp): get_value error: UNKNOWN VALUE: %s" % s_out.replace("\n", " "))

        return val

    def parse_value(self, lst):

        vtest_type = lst[0].upper()
        sval = lst[1]

        if vtest_type == 'INTEGER' or vtest_type == 'GAUGE32' or vtest_type == 'COUNTER32' or vtest_type == 'UNSIGNED32':
            return uglobal.to_int(sval)

        if vtest_type == 'STRING':
            return sval

        if vtest_type == 'TIMETICKS':
            ret = self.re_timeticks.findall(sval)
            if not ret or len(ret) == 0:
                return None

            lst = ret[0]
            if not lst or len(lst) < 1:
                return None

            return uglobal.to_int(lst)

        return None

    def set_value(self, name, value, context):
        ret, err = self.validate_parameter(name, context)

        if ret == False:
            raise TestSuiteValidateError("(snmp): set_value : ERR: '%s'" % err)

        id, nodename, sname = self.parse_name(name)

        param = self.get_parameter(id)
        node = self.get_node(nodename)

        self.snmp_set(param, node, value)

    def snmp_set(self, param, node, value):

        var_name = None

        #  \todo Пока-что поддерживается только test_type INTEGER'''
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
            for err in self.snmpset_errors:
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
        '''
        Создание словаря [oid]=name по указанному mib-файлу
        :param mibfile: mib-файл
        :return: словарь [oid]=name
        '''
        if not os.path.isfile(mibfile):
            raise TestSuiteValidateError(
                "(snmp): get_variables_from_mib : ERR: file not found '%s'" % mibfile)

        cmd = "snmptranslate -Tz -On -m %s" % mibfile
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

            # словарь: [oid] = name
            vars[v[1]] = v[0]

        return vars

    @staticmethod
    def check_oid(oid, mibs):
        for m in mibs:
            if oid in m:
                return True

        return False

    def validate_configuration(self, context):
        """
        Проверка конфигурации snmp
        :param context:
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
        for mibdir in self.mibdirs:
            if not os.path.isdir(mibdir['path']):
                errors.append("\t(snmp): CONF[%s] ERROR: MIB-directory '%s' not found" % (self.confile, mibdir['path']))
                res_ok = False

            mibmask = mibdir['mask']
            if mibmask and len(mibmask) == 0:
                mibmask = '*'

            mdir = "%s/%s" % (mibdir['path'], mibmask)
            for f in glob.glob(mdir):
                if os.path.isfile(f) and f not in mibfiles:
                    mibfiles.append(f)

        if len(mibfiles) > 0:
            mibs = list()  # список словарей [oid]=name
            mibs_names = list()  # список словарей [name]=oid
            for f in mibfiles:
                d = self.get_variables_from_mib(f)
                mibs.append(d)
                d2 = dict((v, k) for k, v in d.iteritems())
                mibs_names.append(d2)

            # Ищем переменные во всех загруженных словарях..
            for oname, var in self.mibparams.items():

                if var['ignoreCheckMIB'] != 0:
                    continue

                if var['OID']:
                    if not self.check_oid(var['OID'], mibs):
                        errors.append("\t(snmp): CONF[%s] ERROR: NOT FOUND OID '%s (%s)' in mibfiles.." % (
                            self.confile, var['OID'], oname))
                        res_ok = False

                if var['ObjectName']:
                    if not self.check_oid(var['ObjectName'], mibs_names):
                        errors.append("\t(snmp): CONF[%s] ERROR: NOT FOUND ObjectName '%s (%s)' in mibfiles.." % (
                            self.confile, var['ObjectName'], oname))
                        res_ok = False

        err = ''
        if len(errors) > 0:
            err = "(snmp): ERRORS: \n %s" % '\n'.join(errors)

        return [res_ok, err]

    def validate_parameter(self, name, context):

        try:
            vname, vnode, fname = self.parse_name(name)
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
