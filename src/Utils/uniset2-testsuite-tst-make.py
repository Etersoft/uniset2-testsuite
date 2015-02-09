#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re

import uniset2

r_test = re.compile(r"^[tT]{1}:[\t\ ]{0,}(.*)$")
r_comment = re.compile(r'^[#]{1,}(.*)$')
r_check = re.compile(r"^[cC]{1}:[\t\ ]{0,}(.*)$")
r_set = re.compile(r"^[sS]{1}:[\t\ ]{0,}(.*)$")
r_msleep = re.compile(r"^[mM]{1}:[\t\ ]{0,}([\d]{1,})$")
r_outlink = re.compile(r"^[oO]{1}:[\t\ ]{0,}(.*)$")
r_link = re.compile(r"^[lL]{1}:[\t\ ]{0,}(.*)$")

isProcTest = False

def proc_comment(f, l):
    e = r_comment.findall(l)
    if len(e) > 0:
        l_out = "<!-- %s -->\n"%e[0]
        f.write(l_out)
        return True

    return False

def proc_check(f, l):
    e = r_check.findall(l)
    if len(e) > 0:
        l_out = "    <check test=\"%s\"/>\n"%e[0].strip()
        f.write(l_out)
        return True

    return False

def proc_set(f, l):
    e = r_set.findall(l)
    if len(e) > 0:
        l_out = "    <action set=\"%s\"/>\n"%e[0].strip()
        f.write(l_out)
        return True

    return False

def proc_outlink(f, l):
    e = r_outlink.findall(l)
    if len(e) > 0:

        p = e[0].split(';');
        if len(p)<=1:
            print "(oulink): Unknown outlink file. (%s)"%l
            l_out = "    <check test=\"outlink\" link=\"%s\" file=\"UNKNOWN\"/>\n"%(p[0].strip())
        else:
            l_out = "    <check test=\"outlink\" link=\"%s\" file=\"%s\"/>\n"%(p[0].strip(),p[1].strip())

        f.write(l_out)
        return True

    return False

def proc_link(f, l):
    e = r_link.findall(l)
    if len(e) > 0:
        l_out = "    <check test=\"link\" link=\"%s\"/>\n"%e[0].strip()
        f.write(l_out)
        return True

    return False

def proc_msleep(f, l):
    e = r_msleep.findall(l)
    if len(e) > 0:
        l_out = "    <action msleep=\"%s\"/>\n"%e[0].strip()
        f.write(l_out)
        return True

    return False

def proc_test(f, l):

    global isProcTest
    e = r_test.findall(l)
    if len(e) > 0:
        if isProcTest:
            f.write("  </test>\n")
            isProcTest = False

        p = e[0].split(';');
        ext = ""
        if len(p)>1:
            ext = p[1]
        l_out = "  <test name=\"%s\" %s>\n"%(p[0].strip(),ext.strip())
        f.write(l_out)
        isProcTest = True
        return True

    return False

def proc_file(fname):

    global isProcTest

    outfilename = os.path.basename(fname) + ".xml"
    bak = str(outfilename + ".bak")
    if os.path.isfile(bak) == False:
        # чтобы "ссылки" не бились, делаем копирование не через rename
        #os.rename(self.fname,str(self.fname+".bak"))
        f_in = open(fname, 'rb')
        f_out = file(bak, 'wb')
        f_in.seek(0)
        f_out.write(f_in.read())
        f_out.close()
        f_in.close()

    # не хорошо, что сперва всё в память грузим
    # но с другой стороны сценарии не бывают оченб большими
    f = open(fname, 'r')
    doc = f.readlines()
    f.close()

    f = open(outfilename, 'w')

    f.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
    f.write("<testsuite>\n")
    f.write("<TestList>\n")

    for l in doc:

        l = l.strip()

        if len(l)==0:
            continue

        # comment
        if proc_comment(f, l):
            continue

        # test
        if proc_test(f, l):
             continue

        # check
        if proc_check(f, l):
            continue

        # set
        if proc_set(f, l):
            continue

        # msleep
        if proc_msleep(f, l):
            continue

        # outlink
        if proc_outlink(f, l):
            continue

        # link
        if proc_link(f, l):
            continue

        # неизвестные пишем тоже в файл..
        f.write(l)

    if isProcTest:
       f.write("  </test>\n")
       isProcTest = False


    f.write("</TestList>\n")
    f.write("</testsuite>\n")
    f.close()


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "Usage: %s file1.tst file2.tst..." % sys.argv[0]
        exit(1)

    argc = len(sys.argv)
    for i in range(1, argc):
        proc_file(sys.argv[i])
