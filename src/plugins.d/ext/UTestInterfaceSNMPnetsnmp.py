#!/usr/bin/env python
# -*- coding: utf-8 -*-

import netsnmp
from UTestInterfaceSNMP import UTestInterfaceSNMP as UTestInterfaceSNMPClass
from TestSuiteGlobal import *
import uniset2.UGlobal as uglobal
from uniset2.pyUExceptions import UException

'''
Реализация SNMP интерфейса на основе python netsnmp
'''


class UTestInterfaceSNMPnetsnmp(UTestInterfaceSNMPClass):
    def __init__(self, **kwargs):

        UTestInterfaceSNMPClass.__init__(self, **kwargs)
        self.itype = "netsnmp"

    def snmp_get(self, param, node):

        var_name = None

        if param['OID']:
            var_name = netsnmp.Varbind(param['OID'])
        elif param['ObjectName']:
            var_name = netsnmp.Varbind(param['ObjectName'])
        else:
            raise TestSuiteValidateError("(netsnmp): get_value : Unknown OID for '%s'" % param['name'])

        ver = node['version']
        if ver == '2c':
            ver = 2

        # netsnmp.verbose = 1
        sess = netsnmp.Session(DestHost=node['ip'],
                               RemotePort=node['port'],
                               Version=ver,
                               Community=param['r_community'],
                               Timeout=uglobal.to_int(node['timeout']),
                               Retries=uglobal.to_int(node['retries'])
                               )

        varlist = netsnmp.VarList(var_name)

        ret = sess.get(varlist)

        if sess.ErrorNum != 0:
            raise TestSuiteValidateError(
                "(netsnmp): '%s' get value error: [%d] '%s'" % (var_name.tag, sess.ErrorNum, sess.ErrorStr))

        if not ret or not ret[0] or len(ret[0]) == 0:
            raise TestSuiteValidateError("(netsnmp): get_value error: NO READ DATA for %s" % var_name.tag)

        return ret[0]

    def snmp_set(self, param, node, value):

        varinfo = None

        if param['OID']:
            varinfo = netsnmp.Varbind(param['OID'], val=value, type='INTEGER')
        elif param['ObjectName']:
            varinfo = netsnmp.Varbind(param['ObjectName'], val=value, type='INTEGER')
        else:
            raise TestSuiteValidateError("(netsnmp): set_value : Unknown OID for '%s'" % param['name'])

        ver = node['version']
        if ver == '2c':
            ver = 2

        sess = netsnmp.Session(DestHost=node['ip'],
                               RemotePort=node['port'],
                               Version=ver,
                               Community=param['w_community'],
                               Timeout=uglobal.to_int(node['timeout']),
                               Retries=uglobal.to_int(node['retries'])
                               )

        varlist = netsnmp.VarList(varinfo)
        sess.set(varlist)

        if sess.ErrorNum == 0:
            return

        raise TestSuiteValidateError(
            "(netsnmp): '%s' set value error: [%d] '%s'" % (varinfo.tag, sess.ErrorNum, sess.ErrorStr))


def uts_create_from_args(**kwargs):
    """
    Создание интерфейса
    :param kwargs: именованные параметры
    :return: объект наследник UTestInterface
    """
    return UTestInterfaceSNMPnetsnmp(**kwargs)


def uts_create_from_xml(xmlConfNode):
    """
    Создание интерфейса
    :param xmlConfNode: xml-узел с настройками
    :return: объект наследник UTestInterface
    """
    return UTestInterfaceSNMPnetsnmp(xmlConfNode=xmlConfNode)


def uts_plugin_name():
    return "netsnmp"
