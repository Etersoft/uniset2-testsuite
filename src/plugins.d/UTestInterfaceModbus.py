#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uniset2.UGlobal import *
from uniset2.pyUModbus import *
from uniset2.pyUExceptions import UException
from UTestInterface import *


class UTestInterfaceModbus(UTestInterface):

    def __init__(self, **kwargs):
        """
        :param kwargs: параметры
        """
        UTestInterface.__init__(self, 'modbus', **kwargs)

        slaveaddr = None
        #  конфигурирование из xmlnode
        if 'xmlConfNode' in kwargs:
            xmlConfNode = kwargs['xmlConfNode']
            slaveaddr = xmlConfNode.prop('mbslave')
            if not slaveaddr:
                raise TestSuiteValidateError("(uniset:init): Not found mbslave='' in %s" % str(xmlConfNode))

        # прямое указание параметра
        elif 'mbslave' in kwargs:
            slaveaddr = kwargs['mbslave']

        if not slaveaddr:
            raise TestSuiteValidateError("(modbus:init): Unknown mbslave address and port")

        ip, port = get_mbslave_param(slaveaddr)

        if not ip or not port:
            raise TestSuiteValidateError("(modbus:init): Unknown ip or port for mbslave='%s'" % (slaveaddr))

        try:
            self.mbi = UModbus()
            self.mbi.prepare(ip, port)
        except UException, e:
            raise TestSuiteValidateError("(modbus:init): ERR: %s " % e.getError())

    @staticmethod
    def parse_name(pname):

        mbaddr, mbreg, mbfunc, nbit, vtest_type = get_mbquery_param(pname, "0x04")
        return [str(mbreg), str(mbaddr), pname]

    def validate_configuration(self, context):
        # todo Реализовать функцию проверки конфигурации
        return [True, ""]

    def validate_parameter(self, name, context):

        try:
            if self.itest_type == "modbus":
                mbaddr, mbreg, mbfunc, nbit, vtest_type = get_mbquery_param(name, "0x04")
                err = []
                if not mbaddr:
                    err.append("Unknown mbaddr")
                if not mbfunc:
                    err.append("Unknown mbfunc")
                if not mbreg:
                    err.append("Unknown mbreg")

                if len(err) > 0:
                    return [False, ', '.join(err)]

                return [True, ""]

        except UException, e:
            return [False, "%s" % e.getError()]

    def get_value(self, name, context):

        try:
            mbaddr, mbreg, mbfunc, nbit, vtest_type = get_mbquery_param(name, "0x04")
            if not mbaddr or not mbreg or not mbfunc:
                raise TestSuiteValidateError(
                    "(modbus:getValue): parse id='%s' failed. Must be 'mbreg@mbaddr:mbfunc:nbit:vtest_type'" % name)

            if self.mbi.isWriteFunction(mbfunc):
                raise TestSuiteValidateError(
                    "(modbus:getValue): for id='%s' mbfunc=%d is WriteFunction. Must be 'read'." % (name, mbfunc))

            return self.mbi.mbread(mbaddr, mbreg, mbfunc, vtest_type, nbit)

        except UException, e:
            raise TestSuiteException(e.getError())

    def set_value(self, name, value, context):
        try:
            # ip,port,mbaddr,mbreg,mbfunc,vtest_type,nbit = ui.get_modbus_param(s_id)
            mbaddr, mbreg, mbfunc, nbit, vtest_type = get_mbquery_param(name, "0x06")
            if not mbaddr or not mbreg or not mbfunc:
                raise TestSuiteValidateError(
                    "(modbus:setValue): parse id='%s' failed. Must be 'mbreg@mbaddr:mbfunc'" % name)

            # print "MODBUS SET VALUE: s_id=%s"%s_id
            if not self.mbi.isWriteFunction(mbfunc):
                raise TestSuiteValidateError(
                    "(modbus:setValue): for id='%s' mbfunc=%d is NOT WriteFunction." % (name, mbfunc))

            self.mbi.mbwrite(mbaddr, mbreg, to_int(value), mbfunc)
            return

        except UException, e:
            raise TestSuiteException(e.getError())


def uts_create_from_args(**kwargs):
    """
    Создание интерфейса
    :param kwargs: именованные параметры
    :return: объект наследник UTestInterface
    """
    return UTestInterfaceModbus(**kwargs)


def uts_create_from_xml(xmlConfNode):
    """
    Создание интерфейса
    :param xmlConfNode: xml-узел с настройками
    :return: объект наследник UTestInterface
    """
    return UTestInterfaceModbus(xmlConfNode=xmlConfNode)


def uts_plugin_name():
    return "modbus"
