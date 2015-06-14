# -*- coding: utf-8 -*-
"""
Created on Thu Jan 22 10:01:23 2015

@author: soukup

Upravil:
   07.04.2015    f:D
       - uprava url pro metadatove sluzby na http://app.iprpraha.cz/geoportal
       - uprava volani systemovych cest na r''
       - "\\" nahrazeno os.sep
"""
import requests
from xml.etree import ElementTree
#import arcpy
import os
import datetime
#import zipfile

class LicenseError(Exception):
    pass

def hbytes(num):
    for x in [' B',' KB',' MB',' GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, ' TB')

def updateXML(docID,ext):
    try:
       print '\t ... provadim update xml ...',docID,ext
       formats=[("GEOJSON","json","GeoJSON","application/geojson"),("SHAPE","shp","Shapefile","application/x-zipped-shp"),("GML","gml","GML","application/gml+xml"),("ACAD","dxf","DXF","application/x-dxf")]

       if "jpg" in ext:
           raster_ext=(".jpg","image/jpeg","JPG")
           raster_ext2=(".jgw","text/plain","JGW")
       else:
           raster_ext=(".tif","image/tiff","TIFF")
           raster_ext2=(".tfw","text/plain","TFW")

                 
       http='http://app.iprpraha.cz/geoportal/rest/document?id='+docID
       response = requests.request('GET', http)
       tree = ElementTree.fromstring(response.content)
       
       http2='http://app.iprpraha.cz/geoportal/csw?REQUEST=GetRecordById&service=CSW&version=2.0.2&ElementSetName=full&Id='+docID
       response2=requests.request('GET', http2)
       tree2 = ElementTree.fromstring(response2.content)
       
       #print http
       #print http2
       
       for identificationInfo in tree.iter('{http://www.isotc211.org/2005/gmd}identificationInfo'):
           nazev=identificationInfo.getchildren()[0].getchildren()[0].getchildren()[0].getchildren()[0].getchildren()[0].text
           abstract=identificationInfo.getchildren()[0].getchildren()[1].getchildren()[0].text
           for MD_datIden in identificationInfo.iter('{http://www.isotc211.org/2005/gmd}MD_DataIdentification'):
               for Cit in MD_datIden.iter('{http://www.isotc211.org/2005/gmd}citation'):
                   for CI_cit in Cit.iter('{http://www.isotc211.org/2005/gmd}CI_Citation'):
                       for date in CI_cit.iter('{http://www.isotc211.org/2005/gmd}CI_Date'):
                           datum=date.getchildren()[0].getchildren()[0].text
                           typ=date.getchildren()[1].getchildren()[0].text
                           if typ=='revision':
                               modi=datum
                               break
                           else:
                               modi=datum
           
       modi_date=datetime.datetime.strptime(modi,'%Y-%m-%d')
       modi_string=modi_date.isoformat("T")+"Z"
               
               #         
       
       #for modified in tree2.iter('{http://purl.org/dc/terms/}modified'):
       #    modi=modified.text
       #    #print modi
           
       for contact in tree.iter('{http://www.isotc211.org/2005/gmd}contact'):
           #jmeno=contact.getchildren()[0].getchildren()[0].getchildren()[0].text
           for electronicMail in contact.iter('{http://www.isotc211.org/2005/gmd}electronicMailAddress'):
               email=electronicMail.getchildren()[0].text
       
       for tag in tree.iter('{http://www.isotc211.org/2005/gmd}identifier'):
           for tag2 in tag.iter('{http://www.isotc211.org/2005/gmd}RS_Identifier'):
               #print tag2    
               RS_Identifier=tag2.getchildren()[0].getchildren()[0].text
               slozka_cur=RS_Identifier.split(".")[0].split("-")[2]
               if slozka_cur=="MAP":
                   slozka_cur="MAP_CUR"
               slozka=slozka_cur.split("_")[0]
               vrstvaFC=RS_Identifier.split(".")[1]
               if vrstvaFC[-2:]=='FC':
                   vrstva=vrstvaFC[:-3]
               else:
                   vrstva=vrstvaFC
       
               
        #tvorba malého Atomu
       root = ElementTree.Element("feed", xmlns="http://www.w3.org/2005/Atom")
       ElementTree.SubElement(root, "title").text = nazev
       ElementTree.SubElement(root, "subtitle").text = abstract
       ElementTree.SubElement(root, "link", href="http://www.geoportalpraha.cz")
       ElementTree.SubElement(root, "link", href="http://opendata.iprpraha.cz/"+slozka_cur.split("_")[1]+"/"+slozka_cur.split("_")[0]+"/"+vrstva+"/"+vrstva+".xml", rel="self")
       ElementTree.SubElement(root, "link", title="Metadata", hreflang="cs", type="application/xml", rel="describedby", href="http://app.iprpraha.cz/geoportal/rest/document?id=%7B"+docID[1:-1]+"%7D")
       #atributová metadata
       try:
           http2='http://app.iprpraha.cz/geoportal/rest/document?id='+RS_Identifier
           response2 = requests.request('GET', http2)
           tree2 = ElementTree.fromstring(response2.content)
           ElementTree.SubElement(root, "link", title="Metadata atributy", hreflang="cs", type="application/xml", rel="describedby", href="http://app.iprpraha.cz/geoportal/rest/document?id="+RS_Identifier)
       except:
           pass
       
       ElementTree.SubElement(root, "link", title="Feed", hreflang="cs", type="application/xml", rel="up", href="http://opendata.iprpraha.cz/feed.xml")
       ElementTree.SubElement(root, "link", title=u"Licenční podmínky", hreflang="cs", type="text/html", rel="license", href="http://www.geoportalpraha.cz/cs/clanek/276/licencni-podminky-pro-otevrena-data")
       ElementTree.SubElement(root, "updated").text=modi_string
       autor=ElementTree.SubElement(root, "author")
       #ElementTree.SubElement(autor, "name").text=jmeno
       ElementTree.SubElement(autor, "name").text=u"Institut plánování a rozvoje hl. m. Prahy"
       ElementTree.SubElement(autor, "email").text=email
       layerID='tag:geoportalpraha.cz,2015-04-01:%7B'+docID[1:-1]+'%7D'
       ElementTree.SubElement(root, "id").text=layerID
       
              
       #konektory
       if vrstva=='BD3' or vrstva=='TER' or vrstva=='mosty':
           
           toDirectory = r'\\odata-storage.ipr.praha.eu\OPENDATA\CUR'+os.sep+slozka+os.sep+vrstva
           soubory=os.listdir(toDirectory+os.sep+"S_JTSK")
           sady=[]    
           pripony=['polygonZ','mp','dgn']
           for soubor in soubory:
               
               if soubor[-12:]=='polygonZ.zip':
                   sady.append(soubor[:-13])
                   
           for sada in sady:
               #print sada
               zaznam=ElementTree.SubElement(root, "entry")
               
               if vrstva!='mosty':
                   ElementTree.SubElement(zaznam, "title").text=nazev+" "+sada                
                   ElementTree.SubElement(zaznam, "id").text=layerID+","+sada+",S_JTSK"
               else:
                   ElementTree.SubElement(zaznam, "title").text=nazev+" S-JTSK"
                   ElementTree.SubElement(zaznam, "id").text=layerID+",S_JTSK"
               for pripona in pripony:
                   soubor=toDirectory+os.sep+"S_JTSK"+os.sep+sada+'_'+pripona+'.zip'
                   if os.path.isfile(soubor):
                       size=os.path.getsize(soubor)
                       if pripona=='polygonZ':
                           titul='Shapefile polygonZ'+" ("+hbytes(size)+")"
                           mime="application/x-zipped-shp"
                       elif pripona=='mp':
                           titul='Shapefile multipatch'+" ("+hbytes(size)+")"
                           mime="application/x-zipped-shp"
                       elif pripona=='dgn':
                           titul='DGN'+" ("+hbytes(size)+")"
                           mime="image/vnd.dgn"
                       ElementTree.SubElement(zaznam, "link",title=titul,rel="alternate",type=mime,href="http://opendata.iprpraha.cz/"+slozka_cur.split("_")[1]+"/"+slozka_cur.split("_")[0]+"/"+vrstva+"/S_JTSK/"+sada+'_'+pripona+'.zip')
                       
               ElementTree.SubElement(zaznam, "updated").text=modi
               ElementTree.SubElement(zaznam, "category", label="S-JTSK", term="http://www.opengis.net/def/crs/EPSG/0/5514")  
           
           
       else:
           for distribution in tree.iter('{http://www.isotc211.org/2005/gmd}distributionFormat'):
               typ=distribution.getchildren()[0].getchildren()[0].getchildren()[0].text
               #print typ
               if typ=="SDE Raster Dataset":
                   toDirectory = r'\\odata-storage.ipr.praha.eu\OPENDATA\CUR'+os.sep+slozka+os.sep+vrstva
                   #print vrstva
                   soubory=os.listdir(toDirectory)
                   for soubor in soubory:
                       if soubor[-4:]==raster_ext[0]:
                           size1=os.path.getsize(toDirectory+os.sep+soubor)
                           size2=os.path.getsize(toDirectory+os.sep+soubor[:-4]+raster_ext2[0])
                           zaznam=ElementTree.SubElement(root, "entry")
                           if soubor[:-4]!=vrstva:
                               ElementTree.SubElement(zaznam, "title").text=nazev+" "+soubor[:-4]
                           else:
                               ElementTree.SubElement(zaznam, "title").text=nazev
                           titul1=raster_ext[2]+" ("+hbytes(size1)+")"
                           titul2=raster_ext2[2]+" ("+hbytes(size2)+")"
                           ElementTree.SubElement(zaznam, "id").text=layerID+","+soubor[:-4]+",S_JTSK"
                           ElementTree.SubElement(zaznam, "link",title=titul1,rel="alternate",type=raster_ext[1],href="http://opendata.iprpraha.cz/"+slozka_cur.split("_")[1]+"/"+slozka_cur.split("_")[0]+"/"+vrstva+"/"+soubor)
                           ElementTree.SubElement(zaznam, "link",title=titul2,rel="related",type=raster_ext2[1],href="http://opendata.iprpraha.cz/"+slozka_cur.split("_")[1]+"/"+slozka_cur.split("_")[0]+"/"+vrstva+"/"+soubor[:-4]+raster_ext2[0]) 
                           ElementTree.SubElement(zaznam, "updated").text=modi
                           ElementTree.SubElement(zaznam, "category", label="S-JTSK", term="http://www.opengis.net/def/crs/EPSG/0/5514")  
               else:        
                   attrs=[]  
                   if tree2 is not None:
                       for feat_attr in tree2.iter('{http://www.isotc211.org/2005/gfc}FC_FeatureAttribute'):
                           local_name = feat_attr.find('{http://www.isotc211.org/2005/gfc}code')
                           attrs.append(local_name.text)
                   #print attrs
                   #print formats
                   for coor_sys in ("S_JTSK","WGS_84"):
                       #print coor_sys
                       zaznam=ElementTree.SubElement(root, "entry")
                      
                       if coor_sys=="S_JTSK":
                           
                           coor_sys_label="S-JTSK"
                           ElementTree.SubElement(zaznam, "title").text=nazev+" "+coor_sys_label
                           ElementTree.SubElement(zaznam, "id").text=layerID+","+coor_sys                        
                           ElementTree.SubElement(zaznam, "category", label="S-JTSK", term="http://www.opengis.net/def/crs/EPSG/0/5514")
                           
                           
                       else:
                           coor_sys_label="WGS 84" 
                           ElementTree.SubElement(zaznam, "title").text=nazev+" "+coor_sys_label 
                           ElementTree.SubElement(zaznam, "id").text=layerID+","+coor_sys     
                           ElementTree.SubElement(zaznam, "category", label="WGS 84", term="http://www.opengis.net/def/crs/EPSG/0/4326")
                           
                       toDirectory = r'\\odata-storage.ipr.praha.eu\OPENDATA\CUR'+os.sep+slozka+os.sep+vrstva

                       soubory=os.listdir(toDirectory+os.sep+coor_sys)
                       for soubor in soubory:
                           ext=soubor[-4:]
                           if ext=='json':
                               extension=formats[0]
                           else:
                               if soubor[-7:-4]=='shp':
                                   extension=formats[1]
                               elif soubor[-7:-4]=='gml':
                                   extension=formats[2]
                               elif soubor[-7:-4]=='dxf':
                                   extension=formats[3]
                           size=os.path.getsize(toDirectory+os.sep+coor_sys+os.sep+soubor)
                           #print soubor[-7:]
                           titul=extension[2]+" ("+hbytes(size)+")"
                           
                           if ext=='json':
                               ElementTree.SubElement(zaznam, "link",title=titul,rel="alternate",href="http://opendata.iprpraha.cz/"+slozka_cur.split("_")[1]+"/"+slozka_cur.split("_")[0]+"/"+vrstva+"/"+coor_sys+"/"+vrstva+".json", type=extension[3])
                           else:
                               ElementTree.SubElement(zaznam, "link",title=titul,rel="alternate",href="http://opendata.iprpraha.cz/"+slozka_cur.split("_")[1]+"/"+slozka_cur.split("_")[0]+"/"+vrstva+"/"+coor_sys+"/"+vrstva+"_"+extension[1]+".zip", type=extension[3])
                           #print titul
                       ElementTree.SubElement(zaznam, "updated").text=modi
       
       tree3 = ElementTree.ElementTree(root)
       tree3.write(toDirectory+os.sep+vrstva+".xml","utf-8", True)

    except Exception as e:
        # If an error occurred, print line number and error message
        import traceback
        import sys
        print datetime.datetime.now().strftime("%H:%M:%S")
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsgs = '\nPYTHON ERRORS:\n Error Info:\n An error occured on line %i' % tb.tb_lineno + '\n Traceback info:\n' + tbinfo
        print str(e)
        print pymsgs

if __name__ == "__main__":
        docID='{6A746C2C-253C-4735-9CFD-2FE6585446B2}'
        ext=['shp']
        updateXML(docID,ext)
