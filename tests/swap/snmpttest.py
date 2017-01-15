#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pysnmp.entity.rfc3413.oneliner import cmdgen


if __name__ == "__main__":

	SNMP_HOST = '192.94.214.205' # 'test.net-snmp.org'
	SNMP_PORT = 161
	SNMP_COMMUNITY = 'demopublic'

	cmdGen = cmdgen.CommandGenerator()

	errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
	cmdgen.CommunityData(SNMP_COMMUNITY),
	cmdgen.UdpTransportTarget((SNMP_HOST, SNMP_PORT)),
	cmdgen.ObjectIdentity('', 'sysUpTime',0)
	)

# cmdgen.ObjectIdentity('SNMPv2-MIB', 'sysUpTime', 0)
	# Check for errors and print out results
	if errorIndication:
		print(errorIndication)
	else:
		if errorStatus:
			print('%s at %s' % (
				errorStatus.prettyPrint(),
				errorIndex and varBinds[int(errorIndex)-1] or '?'))
		else:
			print varBinds
			for name, val in varBinds:
				print('%s = %s' % (name.prettyPrint(), val.prettyPrint()))