# -*- coding: utf-8 -*-
import uniset
from TestSuiteGlobal import *

def get_sinfo(raw, sep='@'):
    if raw == None:
       return ["",""]
       
    v = raw.strip().split(sep)
    if len(v) > 1:
       return [v[0],v[1]]
    return [v[0],""]

def get_node_info( fullname, sep=':' ):
    n1,n2 = get_sinfo(fullname,sep)
    return n1

def select_cbox_element( cbox, val, fnum=0 ):
    if val == None:
       val = ""
    model = cbox.get_model()
    it = model.get_iter_first()
    while it is not None:
         if val.upper() == str(model.get_value(it,fnum)).upper():
            cbox.set_active_iter(it)
            return
         it = model.iter_next(it)

def get_select_cbox_element( cbox, fnum=0 ):
    return cbox.get_model().get_value(cbox.get_active_iter(),fnum)

def find_list_element( model, val, fnum=0 ):
    if val == None:
       val = ""

    it = model.get_iter_first()
    while it is not None:
         if val.upper() == str(model.get_value(it,fnum)).upper():
            return it
         it = model.iter_next(it)

    return None

# чтобы не загружать xml-и каждый раз
# создаём глобальный список загруженных
global_xml = dict()

def create_nodes_box( cbox, confile, selname=None, selID=None, section="nodes" ):

    it = create_nodes_list(cbox.get_model(),confile,selname,selID,section)
    if it != None:
       cbox.set_active_iter(it)

def create_nodes_list( model, confile, selname=None, selID=None, section="nodes" ):
    try:
        if confile in global_xml:
           xml = global_xml[confile]
        else:
           xml = UniXML(confile)
           global_xml[confile] = xml

        model.clear()
        model.append(["",""]) # default node (local node)
        node = xml.findNode(xml.getDoc(),section)[0].children
        it_select = None
        while node != None:
            it = model.append([node.prop("name"),node.prop("id")])

            if selname != None and node.prop("name") == selname:
               it_select = it
            elif selID != None and node.prop("id") == selID:
               it_select = it

            node = xml.nextNode(node)

        return it_select

    except:
        pass

    return None


def create_test_box( cbox, testfile, selname=[], exclude=[], section="TestList" ):

    it = create_test_list(cbox.get_model(),testfile,selname,exclude,section)
    if it != None:
       cbox.set_active_iter(it)

def create_test_list( model, testfile, selname=[], exclude=[], section="TestList" ):
    try:
        if testfile in global_xml:
           xml = global_xml[testfile]
        else:
           xml = UniXML(testfile)
           global_xml[testfile] = xml

        #model.clear()
        node = xml.findNode(xml.getDoc(),section)[0].children
        it_select = None
        while node != None:

            if len(exclude) > 0:
               if node.prop(exclude[0]) == exclude[1]:
                  node = xml.nextNode(node)
                  continue

            it = model.append([node.prop("name"),node])

            if len(selname)>0 and node.prop(selname[0]) == selname[1]:
               it_select = it

            node = xml.nextNode(node)

        return it_select

    except:
        pass

    return None


def init_builder_elements(obj, elist, builder):
    ''' Инициализация переменных из ui файла...
        по списку элементов вида [class field,gladename,xmlname,xml_save_ignore]'''
    for e in elist:
        if e[0] == None or e[1] == None:
           continue
        obj.__dict__[e[0]] = builder.get_object(e[1])

def init_elements_value(obj,elist,snode):
    ''' Инициализация переменных из xml
        по списку элементов вида [(0)class field,(1)gladename,(2)xmlname,(3)xml_save_ignore]'''
    for e in elist:
        if e[0]==None or e[2] == None:
                continue
        cname = str(obj.__dict__[e[0]].__class__.__name__)
        if cname == "SpinButton":
           obj.__dict__[e[0]].set_value(to_int(snode.prop(e[2])))
        elif cname == "Entry":
           obj.__dict__[e[0]].set_text(to_str(snode.prop(e[2])))
        elif cname == "CheckButton":
           obj.__dict__[e[0]].set_active(to_int(snode.prop(e[2])))
        elif cname == "ComboBox":
           set_combobox_element(obj.__dict__[e[0]], to_str(snode.prop(e[2])))
        elif cname == "Label":
           obj.__dict__[e[0]].set_text(to_str(snode.prop(e[2])))

def validate_elements(obj,elist):
    ''' Проверка корректности данны
        по списку элементов вида [class field,gladename,xmlname,xml_save_ignore]'''
    for e in elist:
        if e[0]==None or e[2] == None:
           continue
        cname = str(obj.__dict__[e[0]].__class__.__name__)
        if cname == "Entry":
           s = obj.__dict__[e[0]].get_text()
           if s!="" and check_value_int(s) == False:
              return [False,e[2]]

    return [True,""]

def save2xml_elements_value(obj,elist,snode,setval=None):
   ''' Сохранение переменных в xml-узел
       по списку элементов вида [class field,gladename,xmlname,xml_save_ignore, reset_ignore]'''
   for e in elist:
       if e[0]==None or e[2] == None or e[3]==True:
          continue
       if setval != None:
          if len(e)>4 and e[4]!=True: # проверяем, гнорировать ли при обновлении значением
             continue
          snode.setProp(e[2],setval)
       else:
          cname = str(obj.__dict__[e[0]].__class__.__name__)
          if cname == "CheckButton":
             snode.setProp(e[2],get_cb_param(obj.__dict__[e[0]]))
          elif cname == "Entry":
               snode.setProp(e[2],obj.__dict__[e[0]].get_text())
          elif cname == "Label":
               snode.setProp(e[2],obj.__dict__[e[0]].get_text())
          elif cname == "SpinButton":
               v = obj.__dict__[e[0]].get_value_as_int()
               if v == 0:
                  snode.setProp(e[2],"")
               else:
                  snode.setProp(e[2],str(v))
          elif cname == "ComboBox":
               t = obj.__dict__[e[0]].get_active_text()
               if t == "" or t == "None":
                  snode.setProp(e[2],"")
               else:
                  snode.setProp(e[2],t)

def get_cb_param(checkbutton):
    if checkbutton.get_active():
       return "1"
    return ""

def set_combobox_element(cbox,val,fid=0):
    if val == None:
       val = ""
    model = cbox.get_model()
    it = model.get_iter_first()
    while it is not None:
        if val.upper() == str(model.get_value(it,fid)).upper():
           cbox.set_active_iter(it)
           return
        it = model.iter_next(it)
