# -*- coding: utf-8 -*-
"""Tutorial Plotting WRF 2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1YRZefpwwPyByVaYW4L3mjhCJw01lQfbG

# Import Libraries
"""

from netCDF4 import Dataset
import os
os.environ["PROJ_LIB"] = "C:\\Utilities\\Python\\Anaconda\\Library\\share"; #fixr
import wrf

import numpy as np
import pandas as pd
import metpy
from metpy.units import units

#Menggambar peta
import matplotlib
from matplotlib.cm import get_cmap
import matplotlib.pyplot as plt

#cartopy
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.crs as crs
import cartopy.feature as cfe
from cartopy.feature import NaturalEarthFeature

#basemap
# from mpl_toolkits.basemap import Basemap

# read data nc
nc_eta_kf = Dataset("wrfout_d02_2020-12-02_Eta-KF")
nc_kessler_gf = Dataset("wrfout_d02_2020-12-02_Kessler-GF")
nc_kessler_kf = Dataset("wrfout_d02_2020-12-02_Kessler-KF")
nc_eta_kf.variables

time = wrf.getvar(nc_eta_kf,'Times',timeidx=wrf.ALL_TIMES)
time

rainc = wrf.getvar(nc_eta_kf,'RAINNC',timeidx=wrf.ALL_TIMES)
rainc

#Perhitungan Curah Hujan
def curah_hujan(nc,jam): #jam = perbedaan waktu tiap timestep, nc = dataset wrf yang ingin dicari curah hujannya
    time = wrf.getvar(nc,'Times',timeidx=wrf.ALL_TIMES)
    rainc = wrf.getvar(nc,'RAINC',timeidx=wrf.ALL_TIMES)
    rainsh = wrf.getvar(nc,'RAINSH',timeidx=wrf.ALL_TIMES)
    rainnc = wrf.getvar(nc,'RAINNC',timeidx=wrf.ALL_TIMES)
    prec = rainc.copy()
    for idx,val in enumerate(time.values):
        if idx == 0:
            prec[idx] = 0
        else:
            prec[idx] = (rainc[idx] - rainc[idx-1] + rainsh[idx] - rainsh[idx-1] + rainnc[idx] - rainnc[idx-1]) / jam
    prec.attrs['units'] = 'mm/h'
    prec.attrs['description'] = 'Curah Hujan'
    return prec

prec = curah_hujan(nc_eta_kf,1)
#Waktunya ditambah 7 jam
prec['Time'] = prec['Time'] + np.timedelta64(7, 'h')
prec

"""# Visualisasi"""

for idx,val in enumerate(time.values):
    prec_slice = prec.isel(Time=idx)
    #Create a figure
    fig = plt.figure(figsize=(12,6))
    # Set the GeoAxes to the projection used by WRF
    ax = plt.axes(projection=crs.Mercator())
    # Add coastlines
    ax.coastlines('10m', linewidth=2)

    #Deklarasi variabel plot
    x = wrf.to_np(prec_slice['XLONG'])
    y =wrf.to_np(prec_slice['XLAT'])
    variable = wrf.to_np(prec_slice) #dimensi harus jadi 2d (x,y) tidak ada z atau time
    waktu = pd.to_datetime(prec_slice['Time'].values).strftime('%d %B %Y, %H:%M:%S')
    #Mau mengubah format penulisan waktu?? -> https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior

    # Plot contours
#     lev = np.arange(0,35,5)
    lev = [0,1,5,10,20]
    map = plt.contourf(x,                    #x coordinate
                 y,                    #y coordinate
                 variable,                  #variable to plot
                 transform=crs.PlateCarree(),
                 cmap=get_cmap("Blues"),  #set cmap, reversed() to reversed color order
                 levels=lev,                         #set level
                 extend='max')                      #extend color bar

    # Add a color bar
    cbar = plt.colorbar(ax=ax, shrink=.8)
    cbar.set_label(prec_slice.units)

    # Add the gridlines
    gl=ax.gridlines(color='black')
    gl.bottom_labels, gl.left_labels = True, True
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'size': 10}
    gl.ylabel_style = {'size': 10}

    #add title
    plt.title('Curah Hujan ('+prec_slice.units+')'+'\n'+str(waktu) + ' WIB', fontsize=15)

"""## Mengambil data di 1 Titik"""

"""https://wrf-python.readthedocs.io/en/latest/user_api/generated/wrf.ll_to_xy.html#wrf.ll_to_xy"""
x_y = wrf.ll_to_xy(nc_eta_kf, -1.8, 99.85) #(Melihat index latlon dari nc)
x_y

prec_titik = prec[:,x_y[1].values,x_y[0].values]
prec_titik

tabel = pd.DataFrame({
    'Waktu (WIB)': prec_titik['Time'].values,
    'Curah Hujan':prec_titik.values
})
tabel

"""![image.png](attachment:image.png)"""

ket_hujan = []
for i in tabel['Curah Hujan']:
    if i == 0:
        i = 'Tidak Hujan'
    elif i < 5:
        i = 'Ringan'
    elif 5 <= i < 10:
        i = 'Sedang'
    else:
        i = 'Lebat'
    ket_hujan.append(i)
tabel["Keterangan Hujan Eta-KF"] = ket_hujan
tabel

#Export to excel
tabel.to_excel('Curah Hujan.xlsx',sheet_name='Curah Hujan Hasil WRF')

"""# Verifikasi Data Kategorikal -> Tabel Kontingensi"""

#Membaca Observasi
observasi = pd.read_excel('Ogimet.xlsx', sheet_name = 'Data Ogimet', usecols=['Waktu', 'Prec'])
observasi

#Jika waktu observasi masih dalam utc, ubah ke dalam bentuk WIB dengan cara yang sama seperti sebelumnya
# observasi['Waktu'] += np.timedelta64(7, 'h')
# observasi

ket_hujan = []
for i in observasi['Prec']:
    if i == 0:
        i = 'Tidak Hujan'
    elif i < 5:
        i = 'Ringan'
    elif 5 <= i < 10:
        i = 'Sedang'
    else:
        i = 'Lebat'
    ket_hujan.append(i)
observasi["Keterangan Hujan Observasi"] = ket_hujan
observasi

"""Terdapat perbedaan jumlah data antara observasi dan data model, dapat kita filter waktu yang beririsannya -> Inner Join
![image.png](attachment:image.png)
"""

#Ubah salah satu nama kolom waktu antara keluaran model dan observasi menjadi sama  -> fungsi merge dapat dijalankan
"""https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.rename.html"""
observasi_fix = observasi.rename(columns={"Waktu": "Waktu (WIB)"})
observasi_fix

#Ambil keternagan hujannya saja dan waktu, nilai curah hujan diabaikan
CH = tabel[['Waktu (WIB)','Keterangan Hujan Eta-KF']].merge(observasi_fix[['Waktu (WIB)','Keterangan Hujan Observasi']],
                                                            how='inner', on='Waktu (WIB)')
CH

#Melihat ada jenis apa keterangannya
CH['Keterangan Hujan Eta-KF'].unique()

"""Tabel Kontingensi 2x2
![image.png](attachment:image.png)

Tabel Kontingensi 2x2
![image.png](attachment:image.png)
"""

"""https://scikit-learn.org/stable/modules/generated/sklearn.metrics.multilabel_confusion_matrix.html"""
from sklearn.metrics import multilabel_confusion_matrix
target_names = ["Tidak Hujan",'Ringan','Sedang','Lebat']
mcm = multilabel_confusion_matrix(CH['Keterangan Hujan Observasi'],CH['Keterangan Hujan Eta-KF'], labels=target_names)

tn = mcm[:, 0, 0]
tp = mcm[:, 1, 1]
fn = mcm[:, 1, 0]
fp = mcm[:, 0, 1]
Kinerja = pd.DataFrame({"True-Positif":tp,"True-Negatif":tn,"False-Positif":fp,"False-Negatif":fn}, index=target_names).T
Kinerja['Total']=[tp.sum(),tn.sum(),fp.sum(),fn.sum()]
Kinerja.index.name = 'Kinerja Anemos'
Kinerja

"""![image.png](attachment:image.png)

![image.png](attachment:image.png)

![image.png](attachment:image.png)
"""

POD = []
FAR= []
B = []
TS = []
colnames=[]
for i,col in enumerate(Kinerja.columns[:-1]):
  #POD
  POD.append(round(tp[i]/(tp[i] + fp[i]),2))
  #FAR
  FAR.append(round(tn[i]/(tp[i] + tn[i]),2))
  #Bias
  B.append(round((tp[i] + tn[i])/(tp[i] + fp[i]),2))
  #TS
  TS.append(round(tp[i] / (tp[i]+tn[i]+fp[i]),2))
  colnames.append(col)

Individual_Score = pd.DataFrame({"POD":POD,"FAR":FAR,"Bias":B,"TS":TS}, index=colnames).T
Individual_Score.index.name = 'Kinerja Skema Eta-KF'
Individual_Score

"""![image.png](attachment:image.png)

![image.png](attachment:image.png)
"""

a = Kinerja['Total']['True-Positif']
d = Kinerja['Total']['True-Negatif']
b = Kinerja['Total']['False-Positif']
c = Kinerja['Total']['False-Negatif']

#Overall PC
PC = round((a+d)/(a+b+c+d),2)
#Overall POD/H
H = round(a/(a+c) ,2)
#Overall POFD/F
F = round((b)/(b+d),2)
#Overall KSS/TSS
KSS =round(H - F,2)
#Overall HSS
ref = ((a+b)*(a+c)+(b+d)*(c+d))/(a+b+c+d)**2
HSS = round((PC - ref)/(1 - ref),2)

colnames= ['Overall Score']
Overall_Score = pd.DataFrame({"PC":PC,"KSS":KSS,"HSS":HSS}, index=colnames).T
Overall_Score.index.name = 'Kinerja Skema Eta-KF'
Overall_Score

"""# Referensi RMSE dan Korelasi Pearsons di Python
https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.stats.pearsonr.html
https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_squared_error.html
"""