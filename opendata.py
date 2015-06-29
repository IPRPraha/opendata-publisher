# -*- coding: utf-8 -*-
"""
Created on Thu Feb 12 10:06:06 2015

@author: soukup


Skript slouží k aktualizaci Opendat Atomu o položky z opendat. Pokud nalezne položku opendat,
která byla od posledního spuštění aktualizována, spustí její export.

Externí zdroje:
!    \\agsfs2.ipr.praha.eu\_sde_konektory\gdb2.urm.mepnet.cz     - sde konektory do EGDB IPR
!    \\odata-storage.ipr.rpaha.eu\opendata                       - open data storage IPR
!    http://app.iprpraha.cz/geoportal/                           - metadatová služba IPR
!    http://www.geoportalpraha.cz

    http://www.w3.org/2005/Atom
    http://purl.org/dc/elements/1.1/
    http://www.isotc211.org/2005

Upravil:
   07.04.2015    f:D
       - uprava url pro metadatove sluzby na http://app.iprpraha.cz/geoportal
       - uprava volani systemovych cest na r''
	   
	09.04.2015 Matěj
		-slovník a zpracovávané vrstvy uloženy v separátních json souborech v adresáři conf

	23.06.2015 Matěj
		-emaily dány do separátního souboru v conf
		
"""



import requests
from xml.etree import ElementTree
import datetime
import copy
import pickle
import os
import py_tools.UpdateVrstva
import py_tools.UpdateXml
import py_tools.TeeLog
import py_tools.SendMail
import arcpy
import io
import json

class LicenseError(Exception):
    pass

class ListError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def bigAtom(path,dodelavane=[]):
    chyba=False
	
    with io.open('conf\\od_vrstvy.json', 'r', encoding='utf8') as json_file:
        data=json_file.read()
        vrstvy_name=json.loads(data)
	
    with io.open('conf\\slovnik.json', 'r', encoding='utf8') as json_file:
		data=json_file.read()
		slovnik=json.loads(data)
		
	
    slovnik_docID={}
    vrstvy=[]
    nejsou_od=[]
    for v in vrstvy_name:
        vrstvy.append(v[0])
        
    #loading object which store last update of layers. If last update differs from update date in metadata, layer has to be updated.
    file2=open('vrstvy.obj','rb')
    data=pickle.load(file2)
    file2.close()
    
    

    #nahrazeni nazvuy IDčkem
    vrstvy_ext=copy.deepcopy(vrstvy_name)
    http='http://app.iprpraha.cz/geoportal/csw?REQUEST=GetRecords&service=CSW&version=2.0.2&ElementSetName=full&resultType=results&maxRecords=5000'
    response = requests.request('GET', http)
    tree = ElementTree.fromstring(response.content)
    records=tree.getchildren()[1].getchildren()
    for record in records:
        for identi in record.iter('{http://purl.org/dc/elements/1.1/}identifier'):
            if 'DocID' in identi.attrib["scheme"]:
                docID=identi.text
        http2='http://app.iprpraha.cz/geoportal/rest/document?id='+docID
        response2 = requests.request('GET', http2)
        tree2 = ElementTree.fromstring(response2.content)
        for distributionInfo in tree2.iter('{http://www.isotc211.org/2005/gmd}distributionInfo'):
            for characterString in distributionInfo.iter('{http://www.isotc211.org/2005/gco}CharacterString'):
                if characterString.text=='opendata':
                    for tag in tree2.iter('{http://www.isotc211.org/2005/gmd}identifier'):
                        for tag2 in tag.iter('{http://www.isotc211.org/2005/gmd}RS_Identifier'):
                                RS_Identifier=tag2.getchildren()[0].getchildren()[0].text
                                slozka_cur=RS_Identifier.split(".")[0].split("-")[2]
                                if slozka_cur=="MAP":
                                    slozka_cur="MAP_CUR"                                 
                                vrstvaFC=RS_Identifier.split(".")[1]
                                if vrstvaFC[-2:]=='FC':
                                    vrstva=vrstvaFC[:-3]
                                else:
                                    vrstva=vrstvaFC
                    if vrstva in vrstvy:        
                        index=vrstvy.index(vrstva)
                        if index>-1:
                            vrstvy_ext[index][0]=docID
                            slovnik_docID[docID]=vrstva
                            if vrstva in dodelavane:
                                dodelavane[dodelavane.index(vrstva)]=docID
                    else:
                        chyba=True
                        nejsou_od.append(vrstva)
    vrstvy=[]
    for v in vrstvy_ext:
        vrstvy.append(v[0])
        
    chybne=[]
    
    #tvorba velkeho Atomu
    root = ElementTree.Element("feed", xmlns="http://www.w3.org/2005/Atom")
    ElementTree.SubElement(root, "title").text = u"Otevřená geodata hl. m. Prahy"
    ElementTree.SubElement(root, "link", href="http://www.geoportalpraha.cz")
    ElementTree.SubElement(root, "link", href="http://opendata.iprpraha.cz/feed.xml", rel="self")
    ElementTree.SubElement(root, "link", title=u"Licenční podmínky", hreflang="cs", type="text/html", rel="license", href="http://www.geoportalpraha.cz/cs/clanek/276/licencni-podminky-pro-otevrena-data")
    now=datetime.datetime.utcnow()
    ElementTree.SubElement(root, "updated").text=now.isoformat("T")+"Z"
    autor=ElementTree.SubElement(root, "author")
    ElementTree.SubElement(autor, "name").text=u"Institut plánování a rozvoje hl. m. Prahy"
    ElementTree.SubElement(autor, "email").text="baron@ipr.praha.eu"
    layerID='tag:geoportalpraha.cz,2015-04-01:opendata'
    ElementTree.SubElement(root, "id").text=layerID
        
    http='http://app.iprpraha.cz/geoportal/csw?REQUEST=GetRecords&service=CSW&version=2.0.2&ElementSetName=full&resultType=results&maxRecords=5000'
    response = requests.request('GET', http)
    tree = ElementTree.fromstring(response.content)
    records=tree.getchildren()[1].getchildren()
    
    
    print "dodelavane"
    
    for record in records:

        for identi in record.iter('{http://purl.org/dc/elements/1.1/}identifier'):
            if 'DocID' in identi.attrib["scheme"]:
                docID=identi.text
        
        if docID in vrstvy:
            idx=vrstvy.index(docID)
            extenze=vrstvy_ext[idx][1]
            http2='http://app.iprpraha.cz/geoportal/rest/document?id='+docID
            response2 = requests.request('GET', http2)
            tree2 = ElementTree.fromstring(response2.content)

            for identification_info in tree2.iter('{http://www.isotc211.org/2005/gmd}identificationInfo'):
                for MD_datIden in identification_info.iter('{http://www.isotc211.org/2005/gmd}MD_DataIdentification'):
                    for Cit in MD_datIden.iter('{http://www.isotc211.org/2005/gmd}citation'):
                        for CI_cit in Cit.iter('{http://www.isotc211.org/2005/gmd}CI_Citation'):
                            for date in CI_cit.iter('{http://www.isotc211.org/2005/gmd}CI_Date'):
                                datum=date.getchildren()[0].getchildren()[0].text
                                typ=date.getchildren()[1].getchildren()[0].text
                                if typ=='revision':
                                    modi=datum
                                    break
                                elif typ=='creation':
                                    modi=datum
            modi_date=datetime.datetime.strptime(modi,'%Y-%m-%d')
            
            modi_string=modi_date.isoformat("T")+"Z"

            
            jmeno_vrstvy=slovnik_docID[docID]
            if jmeno_vrstvy in data:
                posledni_date=data[jmeno_vrstvy]
                if posledni_date<modi_date:
                    dodelavane.append(docID)
            else:
                dodelavane.append(docID)
                data[jmeno_vrstvy]=modi_date

            
            if docID in dodelavane:
                print docID
                print path
                try: 
                    py_tools.UpdateVrstva.update(docID,extenze,path)
                    data[jmeno_vrstvy]=modi_date
                    print "hotovo"
                except Exception,e:
                    print str(e)
                    chybne.append(docID)
                    print "chyba"

            py_tools.UpdateXml.updateXML(docID,extenze)

            zaznam=ElementTree.SubElement(root, "entry")
            ElementTree.SubElement(zaznam, "title").text=record.find('{http://purl.org/dc/elements/1.1/}title').text
            ElementTree.SubElement(zaznam, "id").text='tag:iprpraha.cz,2015-04-01:%7B'+docID[1:-1]+'%7D'
            for tag in tree2.iter('{http://www.isotc211.org/2005/gmd}identifier'):
                for tag2 in tag.iter('{http://www.isotc211.org/2005/gmd}RS_Identifier'):
                    RS_Identifier=tag2.getchildren()[0].getchildren()[0].text
                    slozka_cur=RS_Identifier.split(".")[0].split("-")[2]
                    if slozka_cur=="MAP":
                        slozka_cur="MAP_CUR"  
                    slozka=slozka_cur.split("_")[0]
                    cur=slozka_cur.split("_")[1]
                    
                    vrstvaFC=RS_Identifier.split(".")[1]
                    vrstva=vrstvaFC[:-3]
            labels=slovnik[slozka]

            if cur=="GEN":
                    labelc=u"historická"
            else:
                    labelc=u"aktuální"    
              
            
             
            ElementTree.SubElement(zaznam, "category", label=labelc, term=cur)
            ElementTree.SubElement(zaznam, "category", label=labels, term=slozka)
            ElementTree.SubElement(zaznam, "link", title="metadata", hreflang="cs", type="application/xml", rel="describedby", href="http://wgp.urm.cz/geoportal/rest/document?id=%7B"+docID[1:-1]+"%7D")
            ElementTree.SubElement(zaznam, "link", title="Download", hreflang="cs", type="application/xml", href="http://opendata.iprpraha.cz/"+slozka_cur.split("_")[1]+"/"+slozka_cur.split("_")[0]+"/"+vrstva+"/"+vrstva+".xml")
            ElementTree.SubElement(zaznam, "updated").text=modi_string            
            ElementTree.SubElement(zaznam, "summary").text=record.find('{http://purl.org/dc/terms/}abstract').text
    
    file_vrstvy = open('vrstvy.obj', 'wb') 
    pickle.dump(data,file_vrstvy)
    file_vrstvy.close()
    
        
    tree = ElementTree.ElementTree(root)
    tree.write(r'\\odata-storage.ipr.praha.eu\OPENDATA\feed.xml',"utf-8", True)
    print "chybne"   
    print chybne
    if chybne:
        chyba=True
    if nejsou_od:
        raise ListError(nejsou_od)
        
    return chyba
	
if __name__ == "__main__":
    filename='log/log'+datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+'.txt'
    fn = os.path.join(os.path.dirname(os.path.realpath('__file__')), filename)
    print fn
    out=py_tools.TeeLog.Tee2File(fn, 'w')

    try:
        if arcpy.CheckExtension("DataInteroperability") == "Available":
            arcpy.CheckOutExtension("DataInteroperability")
        else:
            # raise a custom exception
            raise LicenseError

        print "Spoustim bigAtom() ..."
        chyba=bigAtom(os.path.dirname(os.path.realpath('__file__')))

    except LicenseError:
        print("nedostupna licence DataInterop")
        chyba=True
    
    except arcpy.ExecuteError:
        msgs = arcpy.GetMessages(2).encode('ascii', 'replace')
        arcpy.AddError(msgs)
        print '\nARCPY ERRORS:\n\t', msgs
        chyba=True
    
    except ListError,e:
        print str(e)
        print "Není v seznamu conf/od_vrstvy.json"
        chyba=True

    except Exception,e:
        print str(e)
        print "Chyba extenze nebo atomu"
        chyba=True

    finally:
        arcpy.CheckInExtension("DataInteroperability")
        out.close()
        if chyba:
            with io.open('conf\\email.json', 'r', encoding='utf8') as json_file:
                data=json_file.read()
                emails=json.loads(data)
                fromEmail=emails[0]
                toEmail=emails[1]
                eServer=emails[2]
            py_tools.SendMail.send_mail( fromEmail, toEmail, 'chyba aktualizace', 'Chyba v aktualizaci', [fn], server=eServer, port=None, username=None, password=None, isTls=None )
            pass
