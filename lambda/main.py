from scipy.spatial import cKDTree
from netCDF4 import Dataset
from sodapy import Socrata
from datetime import date
import pandas as pd
import numpy as np
import requests
import zipfile
import boto3
import time
import gc
import io

start_year = 2002
end_year = 2020

# Revisa si las coordenadas se encuentran en el rango correcto
def check_latlon_bounds(lat, lon, lat_index, lon_index, lat_target, lon_target):
    if(lat[lat_index]>lat_target):
        if(lat_index!=0):
            lat_index = lat_index - 1
    if(lat[lat_index]<lat_target):
        if(lat_index!=len(lat)):
            lat_index = lat_index +1
    if(lon[lon_index]>lon_target):
        if(lon_index!=0):
            lon_index = lon_index - 1
    if(lon[lon_index]<lon_target):
        if(lon_index!=len(lon)):
            lon_index = lon_index + 1

    return [lat_index, lon_index]


# Obtencion de los indices de valores de un array
def get_indexes(data, points):
    data_reshaped = data.filled().reshape(-1, 1)
    tree = cKDTree(data_reshaped)
    query_points = points.to_numpy().reshape(-1, 1)
    _, indexes = tree.query(query_points)

    return indexes


# Datos climaticos por fecha
def get_climate_data_by_date(varname, filehandle, time_values, lat_values, lon_values, year, lat_min, lon_min, lat_max, lon_max):
    # subset in space (lat/lon)
    lathandle           = filehandle.variables['lat']
    lonhandle           = filehandle.variables['lon']
    lat                 = lathandle[:]
    lon                 = lonhandle[:]

    # find indices of target lat/lon/day
    lat_index_min       = (np.abs(lat-lat_min)).argmin()
    lat_index_max       = (np.abs(lat-lat_max)).argmin()
    lon_index_min       = (np.abs(lon-lon_min)).argmin()
    lon_index_max       = (np.abs(lon-lon_max)).argmin()

    [lat_index_min,lon_index_min] = check_latlon_bounds(lat, lon, lat_index_min, lon_index_min, lat_min, lon_min)
    [lat_index_max,lon_index_max] = check_latlon_bounds(lat, lon, lat_index_max, lon_index_max, lat_max, lon_max)

    if(lat_index_min>lat_index_max):
        lat_index_range = range(lat_index_max, lat_index_min+1)
    else:
        lat_index_range = range(lat_index_min, lat_index_max+1)
    if(lon_index_min>lon_index_max):
        lon_index_range = range(lon_index_max, lon_index_min+1)
    else:
        lon_index_range = range(lon_index_min, lon_index_max+1)

    lat = lat[lat_index_range]
    lon = lon[lon_index_range]

    # subset in time
    timehandle          = filehandle.variables['time']
    time                = timehandle[:]
    time_min            = (date(year,1,1)-date(1900,1,1)).days
    time_max            = (date(year,12,31)-date(1900,1,1)).days
    time_index_min      = (np.abs(time-time_min)).argmin()
    time_index_max      = (np.abs(time-time_max)).argmin()
    time_index_range    = range(time_index_min, time_index_max+1)
    time                = timehandle[time_index_range]

    # subset data
    datahandle          = filehandle.variables[varname]
    data                = datahandle[time_index_range, lat_index_range, lon_index_range]

    # Indexes
    time_indexes        = get_indexes(time, time_values)
    lat_indexes         = get_indexes(lat, lat_values)
    lon_indexes         = get_indexes(lon, lon_values)

    return list(data[time_indexes, lat_indexes, lon_indexes].filled(np.nan))


# Datos climaticos de un pais
def get_climate_data_country(df_ff_values, varnames):
    ans = {varname: [] for varname in ["date", "latitude", "longitude"] + varnames}

    for year in range(start_year, end_year + 1):
        # Limit dates
        start_date          = pd.to_datetime(f'{year}-01-01')
        end_date            = pd.to_datetime(f'{year}-12-31')

        # Filtering data
        ff_values           = df_ff_values[df_ff_values["date"] <= end_date]
        ff_values           = ff_values[start_date <= ff_values["date"]]

        # Data
        date_values         = ff_values['date']
        lat_values          = ff_values['latitude']
        lon_values          = ff_values['longitude']

        # Values
        lat_min, lon_min    = lat_values.min(), lon_values.min()
        lat_max, lon_max    = lat_values.max(), lon_values.max()

        ans['date']         += [str(date_.date()) for date_ in date_values]
        ans['latitude']     += list(lat_values.values)
        ans['longitude']    += list(lon_values.values)
        time_values         = (date_values - pd.to_datetime("1900-01-01")).dt.days

        for varname in varnames:
            pathname        = f"http://thredds.northwestknowledge.net:8080/thredds/dodsC/TERRACLIMATE_ALL/data/TerraClimate_{varname}_{year}.nc"
            filehandle      = Dataset(pathname, 'r', format="NETCDF4")
            ans[varname]    += get_climate_data_by_date(
                varname, filehandle, time_values, 
                lat_values, lon_values, year, 
                lat_min, lon_min, lat_max, lon_max
            )

    return ans


# Función que convierte un DataFrame a CSV en memoria
def dataframe_a_csv_buffer(df):
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer


# Lambda function
def lambda_handler(event, context):
    start_time  = time.time()
    dataset_name = event.get("dataset_name", "forest_fire")

    # Definicion del bucket de s3
    s3          = boto3.client('s3')
    bucket_name = 'source-data-bucket-6i2caq'

    # ------------------------------ FOREST FIRE ------------------------------
    if dataset_name == "forest_fire":
        df_ff = None
        for year in range(start_year, end_year + 1):
            url = f"https://firms.modaps.eosdis.nasa.gov/data/country/modis/{year}/modis_{year}_Colombia.csv"

            if df_ff is None:
                df_ff = pd.read_csv(url)
            else:
                df_ff = pd.concat([df_ff, pd.read_csv(url)], ignore_index=True)

        df_ff = pd.merge(
            df_ff.sort_values(by="acq_date")
                .rename(columns={"type": "fire_type", "acq_date": "date"})
                .dropna(),
            pd.DataFrame({
                "fire_type": [0, 1, 2, 3],
                "type": ["presumed vegetation fire", "active volcano", "other static land source", "offshore"]
            }), on="fire_type", how="left").drop(columns=["fire_type"]
        )

        # guardamos los datos
        csv_buffer = dataframe_a_csv_buffer(df_ff)
        s3.put_object(
            Bucket=bucket_name,
            Key='raw/forest_fire/forest_fire.csv',
            Body=csv_buffer.getvalue()
        )

        # eliminamos los datos
        del df_ff
        gc.collect()

    # ------------------------------ NDVI ------------------------------
    if dataset_name == "ndvi":
        url                 = "https://data.humdata.org/dataset/7f2ba5ba-8df1-41cf-ab18-fc1da928a1e5/resource/c06298d9-0d4d-4e40-aecc-abc1da75dc4d/download/col-ndvi-adm2-full.csv"
        df_ndvi             = pd.read_csv(url, low_memory=False)
        df_ndvi             = df_ndvi.drop(index=0)

        start_date          = pd.to_datetime(f'{start_year}-01-01')
        end_date            = pd.to_datetime(f'{end_year}-12-31')

        df_ndvi['date']     = pd.to_datetime(df_ndvi['date'])
        df_ndvi             = df_ndvi[(start_date <= df_ndvi['date']) & (df_ndvi['date'] <= end_date)]

        # ----- DIVIPOLAS -----
        client              = Socrata("www.datos.gov.co", None)
        results             = client.get("gdxc-w37w", limit=2000)
        df_divipolas        = pd.DataFrame.from_records(results)

        fix_number                      = lambda x: float(str(x).replace(',', '.'))
        df_divipolas['latitud']         = df_divipolas['latitud'].apply(fix_number)
        df_divipolas['longitud']        = df_divipolas['longitud'].apply(fix_number)
        df_divipolas.rename(columns={'cod_mpio': 'ADM2_PCODE'}, inplace=True)

        # union
        fix_code                        = lambda x: x.replace("CO", "")
        df_ndvi["ADM2_PCODE"]           = df_ndvi["ADM2_PCODE"].apply(fix_code)
        df_ndvi                         = pd.merge(df_ndvi, df_divipolas, on="ADM2_PCODE", how="left")
        df_ndvi.rename(columns={'latitud': 'latitude', 'longitud': 'longitude'}, inplace=True)

        # eliminamos los datos
        del df_divipolas
        gc.collect()

        response = s3.get_object(Bucket=bucket_name, Key="raw/forest_fire/forest_fire.csv")
        csv_content = response['Body'].read()

        df_ff = pd.read_csv(io.BytesIO(csv_content))
        df_ff_values            = df_ff[['date', 'latitude', 'longitude']].copy()
        df_ff_values['date']    = pd.to_datetime(df_ff_values['date'])

        # eliminamos los datos
        del df_ff
        gc.collect()

        values = {key: [] for key in df_ndvi.columns}
        for year in range(start_year, end_year + 1):
            # Limit dates
            start_date              = pd.to_datetime(f'{year}-01-01')
            end_date                = pd.to_datetime(f'{year}-12-31')

            # Forest fire values
            df_ff_temp              = df_ff_values[(start_date <= df_ff_values['date']) & (df_ff_values['date'] <= end_date)]
            df_ff_temp.reset_index(drop=True, inplace=True)
            lat_values, lon_values  = df_ff_temp['latitude'].values, df_ff_temp['longitude'].values
            time_values = (df_ff_temp['date'] - start_date).dt.days.values

            # Ndvi values
            df_ndvi_temp = df_ndvi[(start_date <= df_ndvi['date']) & (df_ndvi['date'] <= end_date)]
            df_ndvi_temp.reset_index(drop=True, inplace=True)
            lat, lon = df_ndvi_temp['latitude'].values, df_ndvi_temp['longitude'].values
            time = (df_ndvi_temp['date'] - start_date).dt.days.values

            points = np.vstack((lat, lon, time)).T
            tree = cKDTree(points)
            query_points = np.vstack((lat_values, lon_values, time_values)).T
            _, indexes = tree.query(query_points)

            for key in ['latitude', 'longitude', 'date']:
                values[key] += list(df_ff_temp[key].values)

            for key in ['n_pixels', 'vim', 'vim_avg', 'viq']:
                values[key] = np.append(values[key], df_ndvi_temp.iloc[indexes][key].values).astype(float)
            
            del df_ff_temp
            del df_ndvi_temp
            gc.collect()

        # guardamos los datos
        df_ndvi_result      = pd.DataFrame(values).sort_values(by="date")
        csv_buffer          = dataframe_a_csv_buffer(df_ndvi_result)
        s3.put_object(
            Bucket=bucket_name,
            Key='raw/ndvi/ndvi.csv',
            Body=csv_buffer.getvalue()
        )

        # eliminamos los datos
        del df_ndvi_result
        del df_ndvi
        gc.collect()

    # ------------------------------ GLOBAL CLIMATE ------------------------------
    if dataset_name == "global_climate":
        response = s3.get_object(Bucket=bucket_name, Key="raw/forest_fire/forest_fire.csv")
        csv_content = response['Body'].read()

        df_ff = pd.read_csv(io.BytesIO(csv_content))
        df_ff_values            = df_ff[['date', 'latitude', 'longitude']].copy()
        df_ff_values['date']    = pd.to_datetime(df_ff_values['date'])

        # eliminamos los datos
        del df_ff
        gc.collect()

        varnames            = [
            "ws", "vpd", "vap", "tmin", "tmax", "swe", "srad", 
            "soil", "q", "ppt", "pet", "def", "aet", "PDSI"
        ]

        dataset             = get_climate_data_country(df_ff_values.copy(), varnames)
        df_global_climate   = pd.DataFrame(dataset)

        # guardamos los datos
        csv_buffer          = dataframe_a_csv_buffer(df_global_climate)
        s3.put_object(
            Bucket=bucket_name,
            Key='raw/global_climate/global_climate.csv',
            Body=csv_buffer.getvalue()
        )

        # eliminamos los datos
        del df_global_climate
        gc.collect()

    # ------------------------------ POPULATION DENSITY ------------------------------
    if dataset_name == "population_density":
        response = s3.get_object(Bucket=bucket_name, Key="raw/forest_fire/forest_fire.csv")
        csv_content = response['Body'].read()

        df_ff = pd.read_csv(io.BytesIO(csv_content))
        df_ff_values            = df_ff[['date', 'latitude', 'longitude']].copy()
        df_ff_values['date']    = pd.to_datetime(df_ff_values['date'])

        columns         = ['latitude', 'longitude', 'population_density', 'year']
        df_pd_result    = pd.DataFrame(columns=columns)

        for year in range(start_year, end_year + 1):
            # URL del ZIP
            zip_url     = f"https://data.worldpop.org/GIS/Population_Density/Global_2000_2020_1km_UNadj/{year}/COL/col_pd_{year}_1km_UNadj_ASCII_XYZ.zip"

            # Descargar el archivo ZIP
            response    = requests.get(zip_url)
            response.raise_for_status()

            # Leer el ZIP en memoria
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                # Suponiendo que solo hay un archivo en el ZIP
                csv_filename = z.namelist()[0]
                
                # Leer directamente el CSV dentro del ZIP con pandas
                with z.open(csv_filename) as f:
                    df_pd = pd.read_csv(f).rename(columns={
                        'X': 'longitude', 
                        'Y': 'latitude', 
                        'Z': 'population_density'
                    })

            # Limit dates
            start_date              = pd.to_datetime(f'{year}-01-01')
            end_date                = pd.to_datetime(f'{year}-12-31')

            # Filtramos por fecha
            df_ff_temp              = df_ff_values[(start_date <= df_ff_values['date']) & (df_ff_values['date'] <= end_date)]
            lat_values, lon_values  = df_ff_temp['latitude'], df_ff_temp['longitude']

            # Minimos
            lat_min, lat_max        = lat_values.min(), lat_values.max()
            lon_min, lon_max        = lon_values.min(), lon_values.max()

            # Filtramos las latitudes
            df_pd.sort_values(by="latitude", inplace=True)
            df_pd                   = df_pd[lat_min <= df_pd['latitude']]
            df_pd                   = df_pd[df_pd['latitude'] <= lat_max]

            # Filtramos las longitudes
            df_pd.sort_values(by="longitude", inplace=True)
            df_pd                   = df_pd[lon_min <= df_pd['longitude']]
            df_pd                   = df_pd[df_pd['longitude'] <= lon_max]

            # Establecemos valores
            df_pd.reset_index(drop=True, inplace=True)
            lat, lon                    = df_pd['latitude'].to_numpy(), df_pd['longitude'].to_numpy()

            # Hallamos los valores
            points                      = np.vstack((lat, lon)).T
            tree                        = cKDTree(points)
            query_points                = np.vstack((lat_values, lon_values)).T
            _, indexes                  = tree.query(query_points)
            population_density_values   = df_pd.iloc[indexes]['population_density'].to_numpy()

            df_pd_result = pd.concat([
                df_pd_result, 
                pd.DataFrame(
                    {
                        'latitude': lat_values, 
                        'longitude': lon_values,
                        'year': np.full(len(lat_values), year),
                        'population_density': population_density_values
                    }, 
                    columns=columns
                )
            ], ignore_index=True)

            del df_pd
            gc.collect()

        # guardamos los datos
        csv_buffer = dataframe_a_csv_buffer(df_pd_result)
        s3.put_object(
            Bucket=bucket_name,
            Key='raw/population_density/population_density.csv',
            Body=csv_buffer.getvalue()
        )

        # eliminamos los datos
        del df_ff_values
        del df_pd_result
        gc.collect()

    # Duracion del programa
    end_time        = time.time()
    total_time      = end_time - start_time

    minutes         = int(total_time // 60)
    seconds         = int(total_time % 60)

    return {
        'statusCode': 200,
        'body': f'Datasets successfully uploaded in {minutes}m y {seconds}s'
    }