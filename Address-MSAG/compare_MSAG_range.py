import pandas as pd
import os
import geopandas as gpd
from sqlalchemy import create_engine

# read the Intrado extract excel
inpath = r'G:\projects\Address_Points\9-1-1_Net'
file = 'LANEORX2May2021.xls'
#selected_columns = ['ESN', 'STREET', 'CODE', 'LOW', 'HIGH', 'CITY']
selected_columns = ['ESN', 'DI', 'STREET', 'STCODE', 'CTCODE', 'LOW', 'HIGH']

def getIntrado():
    df = pd.read_excel(os.path.join(inpath, file), skiprows = [1])
    df = df[df.columns.drop(list(df.filter(regex='Unnamed')))]
    df['CITY'] = df.COMM.apply(lambda x: adjustCityName(x))
    # export sdf for review
    sdf = df[df.CITY == 'OTHER']
    df = df[df.CITY != 'OTHER']
    df['STCODE'] = df.STREET.apply(lambda x: adjustAddress(x)[1]) 
    df['STREET'] = df.STREET.apply(lambda x: adjustAddress(x)[0])
    dt = getMSAGrange()[2]
    df['CTCODE'] = df['CITY'].map(dt)
    df = df.sort_values(by=selected_columns)[selected_columns]
    df.fillna("",inplace=True)
    df['KEY'] = df.apply(lambda row: str(row.ESN) + '_' + str(row.DI) + '_' + row.STREET + '_' +  row.STCODE + '_' +  row.CTCODE + '_' + str(row.LOW)  + '_' +  str(row.HIGH), axis=1)
    df = df.drop_duplicates(subset=['KEY'])   
    return df, sdf

# split the address with street name and type
def adjustAddress(x):
    code = x.split(' ')[-1]
    codes = ['Rd','Ln','Dr','St','Hwy','Ave','Aly','Way','Ct',
             'Pl','Lp','Ter','Blvd','Cir','Pkwy','Pike']
    codes = list(set(map(str.upper, codes)))
    if code in codes:
        x=x.replace(' '+ code, '')
    else:
        code=''
    return x, code

# change the city names from the column 'COMM'
def adjustCityName(x):
    if x == 'EUG':
        x = 'EUGENE'
    elif x == 'JUNETION CITY':
        x = 'JUNCTION CITY'
    elif x == 'FLORENCE PD-WEST LANE E911':
        x = 'FLORENCE'
    elif x == 'COTTAGE GROVE-SOUTH LANE E911':
        x = 'COTTAGE GROVE'
    elif x == 'OAKRIDGE-EAST LANE E911':
        x = 'OAKRIDGE'
    elif 'LANE' in x or 'IN-' in x:
        x = 'OTHER'
    else:
        x = x
    return x

# read MSA range and address points from RLID
engine = create_engine(   
"mssql+pyodbc:///?odbc_connect="
"Driver%3D%7BODBC+Driver+17+for+SQL+Server%7D%3B"
"Server%3Drliddb.int.lcog.org%2C5433%3B"
"Database%3DRLIDGeo%3B"
"Trusted_Connection%3Dyes%3B"
"ApplicationIntent%3DReadWrite%3B"
"WSID%3Dclwrk4087.int.lcog.org%3B")
def getMSAGrange():
    sql = '''
    SELECT 
    emergency_service_number AS ESN,
    from_house_number AS LOW,
    to_house_number AS HIGH,
    pre_direction_code AS DI,
    street_name AS STREET,
    street_type_code AS STCODE,
    city_name AS CITY,
    city_code AS CTCODE,
    Shape.STAsBinary() AS GEOM
    FROM dbo.MSAG_Range;
    '''
    gdf = gpd.GeoDataFrame.from_postgis(sql, engine, geom_col='GEOM')
    gdf['STREET'] = gdf.STREET.str.upper()
    gdf['STCODE'] = gdf.STCODE.str.upper()
    gdf['CITY'] = gdf.CITY.str.upper()
    dictdf = gdf[['CITY', 'CTCODE']].drop_duplicates(ignore_index=True)
    dt = dict(zip(dictdf.CITY, dictdf.CTCODE))
    
    df = gdf.sort_values(by=selected_columns)[selected_columns]
    df.loc[df.DI.astype(str) == 'nan',  'DI']= None
    df.fillna("", inplace=True)
    df['KEY'] = df.apply(lambda row: str(row.ESN) + '_' + str(row.DI) + '_' + row.STREET + '_' +  row.STCODE + '_' +  row.CTCODE + '_' + str(row.LOW)  + '_' +  str(row.HIGH), axis=1)
    df = df.drop_duplicates(subset=['KEY'])
    return gdf, df, dt

def getAddressPoints():
    sql = '''
    SELECT 
    emergency_service_number AS ESN,
    house_nbr AS HouseNbr,
    street_name AS STREET,
    street_type_code AS CODE,
    city_name AS CITY,
    Shape.STAsBinary() AS GEOM
    FROM dbo.Site_Address;
    '''
    gdf = gpd.GeoDataFrame.from_postgis(sql, engine, geom_col='GEOM')
    gdf['CITY'] = gdf.CITY.str.upper()
    return gdf

# the key is a concatenation of all common addressing elements between the two comparing datasets
def getCommonKeys():
    df1 = getMSAGrange()[1]
    df2 = getIntrado()[0]
    common_keys = [key for key in df1.KEY.unique() if key in df2.KEY.unique()]
    return common_keys

# to mark whether the two datasets share the same key
common_keys = getCommonKeys()
def InCommon(x):
    if x in common_keys:
        res = 1
    else:
        res = 0
    return res

def checkMSAGrange():
    df1 = getMSAGrange()[1]
    df1['D'] = df1.KEY.apply(lambda x: InCommon(x))
    df3 = df1.loc[df1[df1.D==0].index,]
    df2 = getIntrado()[0]
    df2['D'] = df2.KEY.apply(lambda x: InCommon(x))
    df4 = df2.loc[df2[df2.D==0].index,]
    
    # partial keys without certain addressing elements
    # excluding high house number range
    df3['KEYL'] = df3.apply(lambda row: str(row.ESN) + '_' + row.STREET + '_' +  row.CODE + '_' + str(row.LOW) + '_' +  row.CITY, axis=1)
    df4['KEYL'] = df4.apply(lambda row: str(row.ESN) + '_' + row.STREET + '_' +  row.CODE + '_' + str(row.LOW) + '_' +  row.CITY, axis=1)
    # excluding low house number range
    df3['KEYH'] = df3.apply(lambda row: str(row.ESN) + '_' + row.STREET + '_' +  row.CODE + '_' + str(row.HIGH) + '_' +  row.CITY, axis=1)
    df4['KEYH'] = df4.apply(lambda row: str(row.ESN) + '_' + row.STREET + '_' +  row.CODE + '_' + str(row.HIGH) + '_' +  row.CITY, axis=1)
    # excluding house number range
    df3['KEYC'] = df3.apply(lambda row: str(row.ESN) + '_' + row.STREET + '_' +  row.CODE + '_' +  row.CITY, axis=1)
    df4['KEYC'] = df4.apply(lambda row: str(row.ESN) + '_' + row.STREET + '_' +  row.CODE + '_' +  row.CITY, axis=1)
    
    # merge the MSAG range with the Intrado extract on the partial keys
    df5 = df3.merge(df4, how='left', left_on='KEYL', right_on='KEYL')
    df7 = df3.merge(df4, how='left', left_on='KEYH', right_on='KEYH')
    df5.index = df3.index
    df7.index = df3.index
    
    # to update on the MSAG range
    gdf = getMSAGrange()[0]
    
    # write down the match notes
    # 1. exact match - 1; no match - 0
    gdf.loc[df1[df1.D==1].index, 'DIFF'] = 1
    gdf.loc[df1[df1.D==0].index, 'DIFF'] = 0
    gdf.loc[df1[df1.D==1].index, 'MATCH'] = 'Exactly matched'
    
    # 2. no match on the high/low house number range - 2/3
    gdf.loc[df5[~df5.ESN_y.isna()].index, 'MATCH'] = 'High house number range mismatched, Intrado shows ' + df5.loc[~df5.ESN_y.isna(), 'HIGH_y'].astype(str)
    gdf.loc[df5[~df5.ESN_y.isna()].index, 'DIFF'] = 2
    gdf.loc[df7[~df7.ESN_y.isna()].index, 'MATCH'] = 'Low house number range mismatched, Intrado shows ' + df7.loc[~df7.ESN_y.isna(), 'LOW_y'].astype(str)
    gdf.loc[df7[~df7.ESN_y.isna()].index, 'DIFF'] = 3
    
    # 3. missing ESN in the Intrado extract - 4
    missing_esn = [ESN for ESN in gdf.ESN.unique() if ESN not in df2.ESN.unique()]
    gdf.loc[gdf.ESN.isin(missing_esn), 'MATCH'] = 'ESN is not in the Intrado extract'
    gdf.loc[gdf.ESN.isin(missing_esn), 'DIFF'] = 4
    
    # 4. no match on the partial keys without the house number range - 5
    keys = [key for key in df3.KEYC.unique() if key in df4.KEYC.unique()]
    idx1 = gdf[gdf.MATCH.isnull()].index
    idx2 = df3[df3.KEYC.isin(keys)].index
    focus_keys = df3.loc[idx1.intersection(idx2), 'KEYC'].unique()
    low=[]
    high=[]
    for key in focus_keys:
        l = list(df4[df4.KEYC==key].LOW.values)
        h = list(df4[df4.KEYC==key].HIGH.values)
        low.append(l)
        high.append(h)
    
    keydf = pd.DataFrame(list(zip(focus_keys, low, high)),columns =['KEYC', 'LOWC', 'HIGHC'])
    df9 = df3.merge(keydf, how = 'left', left_on = 'KEYC', right_on = 'KEYC')
    df9.index = df3.index
    
    gdf.loc[idx1.intersection(idx2), 'MATCH'] = 'Same address, different house number range, Intrado shows ' + df9.loc[idx1.intersection(idx2), 'LOWC'].astype(str) + ' in low, and ' + df9.loc[idx1.intersection(idx2), 'HIGHC'].astype(str) + ' in high'
    gdf.loc[idx1.intersection(idx2), 'DIFF'] = 5
    
    # 5. no match on the partial keys without the house number range and ESN - 6
    df3['KEYA'] = df3.apply(lambda row: row.STREET + '_' +  row.CODE + '_' +  row.CITY, axis=1)
    df4['KEYA'] = df4.apply(lambda row: row.STREET + '_' +  row.CODE + '_' +  row.CITY, axis=1)
    keys = [key for key in df3.KEYA.unique() if key in df4.KEYA.unique()]
    idx1 = gdf[gdf.MATCH.isnull()].index
    idx2 = df3[df3.KEYA.isin(keys)].index
    focus_keys = df3.loc[idx1.intersection(idx2), 'KEYA'].unique()
    esn=[]
    low=[]
    high=[]
    for key in focus_keys:
        e = list(df4[df4.KEYA==key].ESN.unique())
        l1 = list(df3[df3.KEYA==key].LOW.values)
        l2 = list(df4[df4.KEYA==key].LOW.values)
        l = [l for l in l2 if l not in l1]
        h1 = list(df3[df3.KEYA==key].HIGH.values)
        h2 = list(df4[df4.KEYA==key].HIGH.values)
        h = [h for h in h2 if h not in h1]
        esn.append(e)
        low.append(l)
        high.append(h)
        
    keydf = pd.DataFrame(list(zip(focus_keys, esn, low, high)),columns =['KEYA', 'ESNA', 'LOWA', 'HIGHA'])
    df9 = df3.merge(keydf, how = 'left', left_on = 'KEYA', right_on = 'KEYA')
    df9.index = df3.index
    
    gdf.loc[idx1.intersection(idx2), 'MATCH'] = 'Same address, possibly different house number range (low:' + df9.loc[idx1.intersection(idx2), 'LOWA'].astype(str) + ', high: ' + df9.loc[idx1.intersection(idx2), 'HIGHA'].astype(str) + '; an empty list indicates the same value), and different ESN, Intrado shows ' + df9.loc[idx1.intersection(idx2), 'ESNA'].astype(str)
    gdf.loc[idx1.intersection(idx2), 'DIFF'] = 6
    
    # 6. no match on the partial keys without the house number range, ESN, and road type - 7
    df3['KEYS'] = df3.apply(lambda row: row.STREET + '_' +  row.CITY, axis=1)
    df4['KEYS'] = df4.apply(lambda row: row.STREET + '_' +  row.CITY, axis=1)
    keys = [key for key in df3.KEYS.unique() if key in df4.KEYS.unique()]
    idx1 = gdf[gdf.MATCH.isnull()].index
    idx2 = df3[df3.KEYS.isin(keys)].index
    focus_keys = df3.loc[idx1.intersection(idx2), 'KEYS'].unique()
    esn=[]
    low=[]
    high=[]
    code=[]
    for key in focus_keys:
        e1 = list(df3[df3.KEYS==key].ESN.unique())
        e2 = list(df4[df4.KEYS==key].ESN.unique())
        e = [e for e in e2 if e not in e1]
        l1 = list(df3[df3.KEYS==key].LOW.values)
        l2 = list(df4[df4.KEYS==key].LOW.values)
        l = [l for l in l2 if l not in l1]
        h1 = list(df3[df3.KEYS==key].HIGH.values)
        h2 = list(df4[df4.KEYS==key].HIGH.values)
        h = [h for h in h2 if h not in h1]
        c = list(df4[df4.KEYS==key].CODE.unique())
        esn.append(e)
        low.append(l)
        high.append(h)
        code.append(c)
    
    keydf = pd.DataFrame(list(zip(focus_keys, code, esn, low, high)),columns =['KEYS', 'CODES', 'ESNS', 'LOWS', 'HIGHS'])
    df9 = df3.merge(keydf, how = 'left', left_on = 'KEYS', right_on = 'KEYS')
    df9.index = df3.index
    
    gdf.loc[idx1.intersection(idx2), 'MATCH'] = 'Same address, possibly different house number range (low:' + df9.loc[idx1.intersection(idx2), 'LOWS'].astype(str) + ', high:' + df9.loc[idx1.intersection(idx2), 'HIGHS'].astype(str) + '; an empty list indicates the same value), possibly different ESN (' + df9.loc[idx1.intersection(idx2), 'ESNS'].astype(str) + '), and different road type, Intrado shows ' + df9.loc[idx1.intersection(idx2), 'CODES'].astype(str)
    gdf.loc[idx1.intersection(idx2), 'DIFF'] = 7
    
    gdf.loc[gdf[gdf.MATCH.isnull()].index, 'MATCH'] = 'No match'
    return gdf