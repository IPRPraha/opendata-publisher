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
import datetime
import copy
import os
import arcpy
import zipfile
import shutil

def update(docID,ext,path):
   print path
   try:
       print '\t ... provadim update vrstev ...',docID,ext
       if ext is None:
           formats=[("GEOJSON","json","GeoJSON","application/geojson"),("SHAPE","shp","Shapefile","application/x-zipped-shp"),("GML","gml","GML","application/gml+xml"),("ACAD","dxf","DXF","application/x-dxf")]
       else:
           formats=[("SHAPE","shp","Shapefile","application/x-zipped-shp")]
           if "json" in ext:
               formats.append(("GEOJSON","json","GeoJSON","application/geojson"))
           if "gml" in ext:
               formats.append(("GML","gml","GML","application/gml+xml"))
           if "dxf" in ext:
               formats.append(("ACAD","dxf","DXF","application/x-dxf"))
           if "jpg" in ext:
               raster_ext=(".jpg","image/jpeg","JPG")
           else:
               raster_ext=(".tif","image/tiff","TIFF")

       
       arcpy.env.overwriteOutput=True
       temp=os.path.join(path, "files\\docasne\\")
       temp_zip=os.path.join(path,"files\\tempzip\\")
       temp_sjtsk=os.path.join(path,"files\\S_JTSK2.gdb")
       temp_wgs84=os.path.join(path,"files\\WGS_84.gdb")
       temp_rastr=os.path.join(path,"files\\rastr")

      
       http='http://app.iprpraha.cz/geoportal/rest/document?id='+docID
       response = requests.request('GET', http)
       tree = ElementTree.fromstring(response.content)
       
       http2='http://app.iprpraha.cz/geoportal/csw?REQUEST=GetRecordById&service=CSW&version=2.0.2&ElementSetName=full&Id='+docID
       response2=requests.request('GET', http2)
       tree2 = ElementTree.fromstring(response2.content)

       
       for tag in tree.iter('{http://www.isotc211.org/2005/gmd}identifier'):
           for tag2 in tag.iter('{http://www.isotc211.org/2005/gmd}RS_Identifier'):
     
               RS_Identifier=tag2.getchildren()[0].getchildren()[0].text
               slozka_cur=RS_Identifier.split(".")[0].split("-")[2]
               if slozka_cur=="MAP":
                   slozka_cur="MAP_CUR"
               slozka=slozka_cur.split("_")[0]
               vrstvaFC=RS_Identifier.split(".")[1]
               vrstva=vrstvaFC[:-3]
               in_file=slozka_cur+"."+vrstva

       
              
       #konektory
       workspace=ur"\\agsfs2.ipr.praha.eu\_sde_konektory\gdb2.urm.mepnet.cz"+os.sep+slozka_cur.lower()+"_user@@ipr_gdb2_odb1.sde"
       arcpy.env.workspace=workspace
       arcpy.env.pyramid="NONE"
       arcpy.env.rasterStatistics = "NONE"
       
       for distribution in tree.iter('{http://www.isotc211.org/2005/gmd}distributionFormat'):
           typ=distribution.getchildren()[0].getchildren()[0].getchildren()[0].text

           if typ=="SDE Raster Dataset":
               toDirectory = r'\\odata-storage.ipr.praha.eu\OPENDATA\CUR'+os.sep+slozka+os.sep+vrstva
               slozka_dir=temp_rastr+os.sep+slozka+os.sep+vrstva
               if not os.path.exists(slozka_dir):
                       os.makedirs(slozka_dir)
               if not os.path.exists(toDirectory):
                       os.makedirs(toDirectory)  
               print slozka_dir
               print vrstva
               arcpy.env.outputCoordinateSystem=arcpy.SpatialReference("S-JTSK Krovak EastNorth")
               arcpy.CopyRaster_management(in_file,slozka_dir+os.sep+vrstva+raster_ext[0])
               os.remove(slozka_dir+"\\"+vrstva+raster_ext[0]+".xml")
               shutil.rmtree(toDirectory,True)            
               shutil.copytree(slozka_dir, toDirectory)
               shutil.rmtree(temp_rastr,True)

           else:        
               attrs=[]  
               if tree2 is not None:
                   for feat_attr in tree2.iter('{http://www.isotc211.org/2005/gfc}FC_FeatureAttribute'):
                       local_name = feat_attr.find('{http://www.isotc211.org/2005/gfc}code')
                       attrs.append(local_name.text)
               print attrs
               fms=arcpy.FieldMappings()
               print in_file
               for field in attrs:
                   fm=arcpy.FieldMap()
                   fm.addInputField(in_file,field)
                   fms.addFieldMap(fm)
               arcpy.env.outputCoordinateSystem=arcpy.SpatialReference("S-JTSK Krovak EastNorth")
               arcpy.FeatureClassToFeatureClass_conversion(in_file,temp_sjtsk,vrstva,"",fms)
               arcpy.env.outputCoordinateSystem=arcpy.SpatialReference("WGS 1984")
               arcpy.env.geographicTransformations = "S_JTSK_To_WGS_1984_1"
               arcpy.FeatureClassToFeatureClass_conversion(in_file,temp_wgs84,vrstva,"",fms)

               for coor_sys in ("S_JTSK","WGS_84"):
                   print coor_sys
                   if coor_sys=="S_JTSK":
                       arcpy.env.outputCoordinateSystem=arcpy.SpatialReference("S-JTSK Krovak EastNorth")
                       temp_gdb=temp_sjtsk  
                       
                   else:
                       arcpy.env.outputCoordinateSystem=arcpy.SpatialReference("WGS 1984")
                       temp_gdb=temp_wgs84
                      

                   for extension in formats:
                       print extension                  
                       cesta=extension[0]+ur","+temp+vrstva+os.sep+coor_sys+os.sep+extension[1]+ur"\\"+vrstva+"."+extension[1]
                                      
                       if extension[0]=="SHAPE":
                           directory=temp+vrstva+os.sep+coor_sys+os.sep+extension[1]
                                                  
                           if not os.path.exists(directory):
                               os.makedirs(directory)                  
                           arcpy.FeatureClassToFeatureClass_conversion(temp_gdb+os.sep+vrstva,directory,vrstva+"."+extension[1])
                       else:
                           if extension[0]=="ACAD":
                               cesta=cesta+",\"RUNTIME_MACROS,\"\"DEFAULT_ATTR_STORAGE,external_attributes,VERSION,Release2004,TEMPLATEFILE_GUI,\"\",META_MACROS,\"\"DestDEFAULT_ATTR_STORAGE,external_attributes,DestVERSION,Release2004,DestTEMPLATEFILE_GUI,\"\",METAFILE,ACAD,COORDSYS,,__FME_DATASET_IS_SOURCE__,false\""
                               directory=temp+vrstva+os.sep+coor_sys+os.sep+extension[1]
                               if not os.path.exists(directory):
                                   os.makedirs(directory)
                           elif extension[0]=="GEOJSON":
                               cesta=cesta+",\"RUNTIME_MACROS,\"\"WRITER_CHARSET,UTF-8,WRITE_BOM,No,STRICT_SPEC,Yes,JSONP_FUNC_NAME,\"\",META_MACROS,\"\"DestWRITER_CHARSET,UTF-8,DestWRITE_BOM,No,DestSTRICT_SPEC,Yes,DestJSONP_FUNC_NAME,\"\",METAFILE,GEOJSON,COORDSYS,,__FME_DATASET_IS_SOURCE__,false\""
                           print temp_gdb+os.sep+vrstva
                           print cesta
                           try:
                               arcpy.QuickExport_interop(temp_gdb+os.sep+vrstva,cesta)
                           except Exception as e:
                               print e
                       directory=temp+vrstva+os.sep+coor_sys+os.sep+extension[1]+os.sep
                       os.chdir(directory) 
                       
                       slozka_zip=temp_zip+vrstva+os.sep+coor_sys+os.sep
                       if not os.path.exists(slozka_zip):
                               os.makedirs(slozka_zip)
                       
                       if extension[0]=="GEOJSON":
                           soubory=os.listdir(os.getcwd())
                           for soubor in soubory:
                               shutil.copyfile(soubor,slozka_zip+vrstva+".json")

                       else:
                           with zipfile.ZipFile(slozka_zip+vrstva+"_"+extension[1]+".zip",'w',zipfile.ZIP_DEFLATED,True) as myzip:
                               soubory=os.listdir(os.getcwd())
                               for soubor in soubory:
                                   if soubor[-3:]!="xml":
                                       myzip.write(soubor)

               #toDirectory = "\\\odata-storage\\OPENDATA\\CUR\\"+slozka+ur"\\"+vrstva
               toDirectory=os.path.join(r'\\odata-storage.ipr.praha.eu\OPENDATA\CUR',slozka,vrstva)
               print "zahajuji kopirovani"
               #fromDirectory = temp_zip+vrstva
               fromDirectory=os.path.join(temp_zip,vrstva)
               print toDirectory   
               print fromDirectory
               shutil.rmtree(toDirectory,True)
               shutil.copytree(fromDirectory, toDirectory)
                   
               print "dokopirovano, ted mazani"
               #os.chdir("C:\\")
               os.chdir(path)
               shutil.rmtree(temp)
               shutil.rmtree(temp_zip)
               arcpy.env.workspace=temp_sjtsk
               fcList = arcpy.ListFeatureClasses()
               for fc in fcList:
                   arcpy.Delete_management(fc)
               arcpy.env.workspace=temp_wgs84
               fcList = arcpy.ListFeatureClasses()
               for fc in fcList:
                   arcpy.Delete_management(fc)

   except arcpy.ExecuteError:
      msgs = arcpy.GetMessages(2).encode('ascii', 'replace')      #.decode('utf-8')
      arcpy.AddError(msgs)
      print '\nARCPY ERRORS:\n\t', msgs
        
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
   docID=[]
   ext=[]
   path=r''
   update(docID,ext,path)

