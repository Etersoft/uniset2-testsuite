#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uniset2.UGlobal import *
from uniset2.pyUModbus import *
from uniset2.pyUExceptions import UException
from UTestInterface import *


class UTestInterfaceModbus(UTestInterface):
    def __init__(self, ip, port):
        UTestInterface.__init__(self, 'modbus')

        self.mbi = UModbus()
        self.mbi.prepare(ip, port)

    @staticmethod
    def parseID(self, pname):

        mbaddr, mbreg, mbfunc, nbit, vtype = get_mbquery_param(pname, "0x04")
        return [str(mbreg), str(mbaddr), pname]

    def validateConfiguration(self):
        # todo Реализовать функцию проверки конфигурации
        return [True, ""]

    def validateParameter(self, pname):

        try:
            if self.itype == "modbus":
                mbaddr, mbreg, mbfunc, nbit, vtype = get_mbquery_param(pname, "0x04")
                err = []
                if mbaddr == None:
                    err.append("Unknown mbaddr")
                if mbfunc == None:
                    err.append("Unknown mbfunc")
                if mbreg == None:
                    err.append("Unknown mbreg")

                if len(err) > 0:
                    return [False, ', '.join(err)]

                return [True, ""]

        except UException, e:
            return [False, "%s" % e.getError()]

    def getValue(self, name):

        try:
            mbaddr, mbreg, mbfunc, nbit, vtype = get_mbquery_param(name, "0x04")
            if mbaddr == None or mbreg == None or mbfunc == None:
                raise TestSuiteValidateError(
                    "(modbus:getValue): parse id='%s' failed. Must be 'mbreg@mbaddr:mbfunc:nbit:vtype'" % name)

            if self.mbi.isWriteFunction(mbfunc) == True:
                raise TestSuiteValidateError(
                    "(modbus:getValue): for id='%s' mbfunc=%d is WriteFunction. Must be 'read'." % (name, mbfunc))

            return self.mbi.mbread(mbaddr, mbreg, mbfunc, vtype, nbit)

        except UException, e:
            raise TestSuiteException(e.getError())

    def setValue(self, name, value, supplierID):
        try:
            # ip,port,mbaddr,mbreg,mbfunc,vtype,nbit = ui.get_modbus_param(s_id)
            mbaddr, mbreg, mbfunc, nbit, vtype = get_mbquery_param(name, "0x06")
            if mbaddr == None or mbreg == None or mbfunc == None:
                raise TestSuiteValidateError(
                    "(modbus:setValue): parse id='%s' failed. Must be 'mbreg@mbaddr:mbfunc'" % name)

            # print "MODBUS SET VALUE: s_id=%s"%s_id
            if self.mbi.isWriteFunction(mbfunc) == False:
                raise TestSuiteValidateError(
                    "(modbus:setValue): for id='%s' mbfunc=%d is NOT WriteFunction." % (name, mbfunc))

            self.mbi.mbwrite(mbaddr, mbreg, to_int(value), mbfunc)
            return

        except UException, e:
            raise TestSuiteException(e.getError())
