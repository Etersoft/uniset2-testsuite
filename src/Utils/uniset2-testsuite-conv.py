#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re


# ([\w@]{1,})([!><]{0,}[=]{0,})(\d{1,})")
r_id = re.compile(r'(id=["\']+([\w@:\ ]{1,})["\']+)')
# val="" может быть и текстовым, если это 'шаблон' (для replace)
r_val = re.compile(r'(val=["\']+([\w\ ]{1,})["\']+)')
r_id_set = re.compile(r'(set=["\']+([\w@:=,\ ]{1,})["\']+)')
r_msec = re.compile(r'(msec=["\']+([\d\ ]{1,})["\']+)')

r_ev = re.compile(r'(test=[\'"]+event[\'"]+)')
r_true = re.compile(r'(test=[\'"]+true[\'"]+)')
r_false = re.compile(r'(test=[\'"]+false[\'"]+)')
r_eq = re.compile(r'(test=[\'"]+equal[\'"]+)')
r_great = re.compile(r'(test=[\'"]+great[\'"]+)')
r_less = re.compile(r'(test=[\'"]+less[\'"]+)')
r_set = re.compile(r'(name=[\'"]+set[\'"]+)')
r_mset = re.compile(r'(name=[\'"]+multiset[\'"]+)')
r_msleep = re.compile(r'(name=[\'"]+msleep[\'"]+)')


def id_val_replace(f, l, r, tname, field='test'):
    e = r.findall(l)
    if len(e) > 0:
        s_id = r_id.findall(l)
        s_val = r_val.findall(l)
        l = l.replace(s_id[0][0], '');
        l = l.replace(s_val[0][0], '');
        l = l.replace(e[0], '%s="%s%s%s"' % (field, s_id[0][1], tname, s_val[0][1]))
        l = l.replace('  ', ' ')
        l = l.replace('val2=', 'rval=')
        f.write(l)
        return True

    return False


def id_replace(f, l, r, tname, field='test'):
    e = r.findall(l)
    if len(e) > 0:
        s_id = r_id.findall(l)
        l = l.replace(s_id[0][0], '');
        l = l.replace(e[0], '%s="%s%s"' % (field, s_id[0][1], tname))
        l = l.replace('  ', ' ')
        f.write(l)
        return True

    return False


def multiset_replace(f, l, r, field='set'):
    e = r.findall(l)
    if len(e) > 0:
        s_id = r_id_set.findall(l)
        l = l.replace(s_id[0][0], '');
        l = l.replace(e[0], '%s="%s"' % (field, s_id[0][1]))
        l = l.replace('  ', ' ')
        f.write(l)
        return True

    return False


def msleep_replace(f, l, r):
    e = r.findall(l)
    if len(e) > 0:
        msec = r_msec.findall(l)
        l = l.replace(msec[0][0], '');
        l = l.replace(e[0], 'msleep="%s"' % (msec[0][1]))
        l = l.replace('  ', ' ')
        f.write(l)
        return True

    return False


def proc_file(fname):
    bak = str(fname + ".bak")
    if os.path.isfile(bak) == False:
        # чтобы "ссылки" не бились, делаем копирование не через rename
        #os.rename(self.fname,str(self.fname+".bak"))
        f_in = open(fname, 'rb')
        f_out = file(bak, 'wb')
        f_in.seek(0)
        f_out.write(f_in.read())
        f_out.close()
        f_in.close()

    f = open(fname, 'rb')
    doc = f.readlines()
    f.close()

    f = open(fname, 'wb')
    for l in doc:
        # EVENT
        if id_val_replace(f, l, r_ev, '='):
            continue

        # EQUAL
        if id_val_replace(f, l, r_eq, '='):
            continue

        # GREAT
        if id_val_replace(f, l, r_great, ">="):
            continue

        # LESS
        if id_val_replace(f, l, r_less, "<="):
            continue

        # TRUE
        if id_replace(f, l, r_true, "!=0"):
            continue

        # FALSE
        if id_replace(f, l, r_false, "=0"):
            continue

        # SET
        if id_val_replace(f, l, r_set, "=", 'set'):
            continue

        # MULTISET
        if multiset_replace(f, l, r_mset, 'set'):
            continue

        # MSLEEP
        if msleep_replace(f, l, r_msleep):
            continue

        f.write(l)

    f.close()


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "Usage: %s file1.xml file2.xml ..." % sys.argv[0]
        exit(1)

    argc = len(sys.argv)
    for i in range(1, argc):
        print "convert '%s'.." % sys.argv[i]
        proc_file(sys.argv[i])
