#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pysnmp
from pysnmp.entity.rfc3413.oneliner import cmdgen as snmp
from UTestInterfaceSNMP import UTestInterfaceSNMP as UTestInterfaceSNMPClass
from TestSuiteGlobal import *
import uniset2.UGlobal as uglobal
from uniset2.pyUExceptions import UException

'''
Реализация SNMP интерфейса на основе pysnmp
'''


class UTestInterfaceSNMPpysnmp(UTestInterfaceSNMPClass):
    def __init__(self, **kwargs):

        UTestInterfaceSNMPClass.__init__(self, **kwargs)
        self.itype = "pysnmp"
        self.snmp = snmp.CommandGenerator()

    @staticmethod
    def get_mp_model(protocolVersion, defval=1):

        # преобразуем версию в число для pysnmp
        # см. http://pysnmp.sourceforge.net/docs/pysnmp-hlapi-tutorial.html#choosing-snmp-protocol-and-credentials

        if protocolVersion == '1':  # SNMPv1
            return 0

        if protocolVersion == '2' or protocolVersion == '2c':  # SNMPv2c
            return 1

        return defval

    def snmp_get(self, param, node):

        var_name = None
        ver = self.get_mp_model(node['version'])

        if param['OID']:
            var_name = snmp.MibVariable(param['OID'])
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

            var_name = snmp.MibVariable(pname, vname, vnum)
        else:
            raise TestSuiteValidateError("(snmp): 'getValue' Unknown OID for '%s'" % param['name'])

        community = snmp.CommunityData(param['r_community'], mpModel=ver)
        transport = snmp.UdpTransportTarget((node['ip'], node['port']), timeout=node['timeout'],
                                            retries=node['retries'])

        errorIndication, errorStatus, errorIndex, varBinds = self.snmp.getCmd(
            community,
            transport,
            var_name
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

    def snmp_set(self, param, node, value):

        var_name = None
        ver = self.get_mp_model(node['version'])

        if param['OID']:
            var_name = snmp.MibVariable(param['OID'])
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

            var_name = snmp.MibVariable(pname, vname, vnum)
        else:
            raise TestSuiteValidateError("(snmp): 'getValue' Unknown OID for '%s'" % param['name'])

        community = snmp.CommunityData(param['w_community'], mpModel=ver)
        transport = snmp.UdpTransportTarget((node['ip'], node['port']), timeout=node['timeout'],
                                            retries=node['retries'])

        errorIndication, errorStatus, errorIndex, varBinds = self.snmp.setCmd(
            community,
            transport,
            (var_name, uglobal.to_int(value))
        )

        if errorIndication:
            raise TestSuiteValidateError("(snmp): set_value : ERR: %s" % errorIndication)

        if errorStatus:
            raise TestSuiteValidateError("(snmp): set_value : ERR: %s at %s " % (
                errorStatus.prettyPrint(), errorIndex and varBinds[int(errorIndex) - 1] or '?'))

        if len(varBinds) <= 0:
            raise TestSuiteValidateError("(snmp): set_value : ERR: NO DATA?!!")

        ret_varname, val = varBinds[0]

        if not val:
            raise TestSuiteValidateError(
                "(snmp): set_value : UNKNOWN ERROR : for set %s = %s!" % (str(ret_varname), str(value)))

        if uglobal.to_str(val) != uglobal.to_str(value):
            raise TestSuiteValidateError(
                "(snmp): set_value : ERR: %s for set %s = %s!" % (str(val), str(ret_varname), str(value)))


def uts_create_from_args(**kwargs):
    """
    Создание интерфейса
    :param kwargs: именованные параметры
    :return: объект наследник UTestInterface
    """
    return UTestInterfaceSNMPpysnmp(**kwargs)


def uts_create_from_xml(xmlConfNode):
    """
    Создание интерфейса
    :param xmlConfNode: xml-узел с настройками
    :return: объект наследник UTestInterface
    """
    return UTestInterfaceSNMPpysnmp(xmlConfNode=xmlConfNode)


def uts_plugin_name():
    return "pysnmp"
