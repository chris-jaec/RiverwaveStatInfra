import json
import os
from urllib.request import urlopen

import boto3
from boto3.dynamodb.conditions import Attr
from bs4 import BeautifulSoup
import csv

from src.utilfuncs import (
    get_db_time_str_from_datetime_obj,
    get_datetime_obj_from_db_time_str,
    get_timestamp_from_db_time_str,
    get_time_difference,
    transform_theriverwave_time,
    transform_swiss_time,
    tranform_values,
    time_now
)

TIME_NOW = time_now()
DEF_TIME_INTERVAL = 180
TTL_INTERVAL = 60*60*24*30


class RiverwaveStatDb(object):

    def __init__(self, riverwave_name, region='eu-central-1', stage='dev'):

        dynamodb = boto3.resource('dynamodb', region_name=region)

        overview_table = dynamodb.Table(f'riverwavestat-{stage}-overview')

        wave_info = overview_table.scan(
            Select='ALL_ATTRIBUTES',
            FilterExpression=Attr('name').contains(riverwave_name)
        )

        self.name = wave_info["Items"][0]["name"]
        self.enabled = wave_info["Items"][0]["enabled"]
        self.enabled_water_temperature = wave_info["Items"][0]["data"]["water_temperature"]["enabled"]
        self.enabled_water_level = wave_info["Items"][0]["data"]["water_level"]["enabled"]
        self.enabled_water_runoff = wave_info["Items"][0]["data"]["water_runoff"]["enabled"]

        if self.enabled_water_level:
            self.table_water_level = dynamodb.Table(f'riverwavestat-{stage}-{self.name}-water-level')

        if self.enabled_water_temperature:
            self.table_water_temperature = dynamodb.Table(f'riverwavestat-{stage}-{self.name}-water-temperature')

        if self.enabled_water_runoff:
            self.table_water_runoff = dynamodb.Table(f'riverwavestat-{stage}-{self.name}-water-runoff')

    def get_data(self, time_interval=DEF_TIME_INTERVAL):

        data = {}

        if self.enabled_water_level:
            data["water_level"] = self.get_data_water_level(time_interval)

        if self.enabled_water_temperature:
            data["water_temperature"] = self.get_data_water_temperature(time_interval)

        if self.enabled_water_runoff:
            data["water_runoff"] = self.get_data_water_runoff(time_interval)

        return data

    def get_data_water_level(self, time_interval=DEF_TIME_INTERVAL):
        pass

    def get_data_water_temperature(self, time_interval=DEF_TIME_INTERVAL):
        pass

    def get_data_water_runoff(self, time_interval=DEF_TIME_INTERVAL):
        pass

    def write_data(self, time_interval=DEF_TIME_INTERVAL):

        if self.enabled_water_level:
            data_water_level = self.get_data_water_level(time_interval)

            for datetime_str, value in data_water_level.items():
                self.table_water_level.put_item(
                    Item={
                        'datetime': datetime_str,
                        'value': value,
                        'timestamp': get_timestamp_from_db_time_str(datetime_str),
                        'TTL': get_timestamp_from_db_time_str(datetime_str) + TTL_INTERVAL
                    }
                )

        if self.enabled_water_temperature:
            data_water_temperature = self.get_data_water_temperature(time_interval)

            for datetime_str, value in data_water_temperature.items():
                self.table_water_temperature.put_item(
                    Item={
                        'datetime': datetime_str,
                        'value': value,
                        'timestamp': get_timestamp_from_db_time_str(datetime_str),
                        'TTL': get_timestamp_from_db_time_str(datetime_str) + TTL_INTERVAL
                    }
                )

        if self.enabled_water_runoff:
            data_water_runoff = self.get_data_water_runoff(time_interval)

            for datetime_str, value in data_water_runoff.items():
                self.table_water_runoff.put_item(
                    Item={
                        'datetime': datetime_str,
                        'value': value,
                        'timestamp': get_timestamp_from_db_time_str(datetime_str),
                        'TTL': get_timestamp_from_db_time_str(datetime_str) + TTL_INTERVAL
                    }
                )


class EisbachStatDb(RiverwaveStatDb):

    def __init__(self, region='eu-central-1', stage='dev'):
        super().__init__(riverwave_name="eisbach", region=region, stage=stage)

    def get_data_water_level(self, time_interval=DEF_TIME_INTERVAL):
        url_water_lvl = "https://www.hnd.bayern.de/pegel/donau_bis_kelheim/muenchen-himmelreichbruecke-16515005/tabelle?methode=wasserstand&setdiskr=15"
        water_lvl_data = self.get_eisbach_data(url_water_lvl, time_interval)
        return water_lvl_data

    def get_data_water_temperature(self, time_interval=DEF_TIME_INTERVAL):
        url_water_temperature = "https://www.gkd.bayern.de/de/fluesse/wassertemperatur/kelheim/muenchen-himmelreichbruecke-16515005/messwerte/tabelle"
        water_temperature_data = self.get_eisbach_data(url_water_temperature, time_interval)
        return water_temperature_data

    def get_data_water_runoff(self, time_interval=DEF_TIME_INTERVAL):
        url_water_runoff = "https://www.hnd.bayern.de/pegel/donau_bis_kelheim/muenchen-himmelreichbruecke-16515005/tabelle?methode=abfluss&setdiskr=15"
        water_runoff_data = self.get_eisbach_data(url_water_runoff,
                                                  time_interval)
        return water_runoff_data

    def get_eisbach_data(self, url, time_interval):
        page = urlopen(url)
        html_bytes = page.read()
        html = html_bytes.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        eisbach_data_arr = soup.find_all("tr", class_="row")

        data = {}
        for eisbach_data in eisbach_data_arr:
            eisbach_data = eisbach_data.find_all("td")
            time = eisbach_data[0].get_text()
            value = eisbach_data[1].get_text()

            if value == "--":
                continue

            value = tranform_values(value)

            time_parsed = get_datetime_obj_from_db_time_str(time)

            if (get_time_difference(TIME_NOW, time_parsed) <
                    time_interval):
                data[time] = value

        return data


class TheRiverwaveStatDb(RiverwaveStatDb):

    def __init__(self, region='eu-central-1', stage='dev'):
        super().__init__(riverwave_name="theriverwave", region=region,
                         stage=stage)

    def get_data_water_level(self, time_interval=DEF_TIME_INTERVAL):
        url_water_lvl = "https://hydro.ooe.gv.at/daten/internet/stations/OG/4470/S/week.json"
        water_lvl_data = self.get_theriverwave_data(url_water_lvl, time_interval)
        return water_lvl_data

    def get_data_water_temperature(self, time_interval=DEF_TIME_INTERVAL):
        url_water_temp = "https://hydro.ooe.gv.at/daten/internet/stations/OG/4470/WT/week.json"
        water_temperature_data = self.get_theriverwave_data(url_water_temp, time_interval)
        return water_temperature_data

    def get_theriverwave_data(self, url, time_interval):
        page = urlopen(url)
        html_bytes = page.read()
        html = html_bytes.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        body = soup.get_text()

        theriverwave_data_arr = json.loads(body)[0]['data']
        theriverwave_data_arr.reverse()

        data = {}
        for theriverwave_data in theriverwave_data_arr:
            time_parsed = transform_theriverwave_time(theriverwave_data[0])
            time = get_db_time_str_from_datetime_obj(time_parsed)
            value = theriverwave_data[1]
            value = tranform_values(value)

            if (get_time_difference(TIME_NOW, time_parsed) <
                    time_interval):
                data[time] = value

        return data


class FuchslochwelleStatDb(RiverwaveStatDb):

    def __init__(self, region='eu-central-1', stage='dev'):
        super().__init__(riverwave_name="fuchslochwelle", region=region,
                         stage=stage)

    def get_data_water_level(self, time_interval=DEF_TIME_INTERVAL):
        url_water_lvl = "https://www.hnd.bayern.de/pegel/donau_bis_kelheim/nuernberg-lederersteg-24225000/tabelle?methode=wasserstand&setdiskr=15"
        water_lvl_data = self.get_fuchslochwelle_data(url_water_lvl, time_interval)
        return water_lvl_data

    def get_data_water_runoff(self, time_interval=DEF_TIME_INTERVAL):
        url_water_runoff = "https://www.hnd.bayern.de/pegel/donau_bis_kelheim/nuernberg-lederersteg-24225000/tabelle?methode=abfluss&setdiskr=15"
        water_runoff_data = self.get_fuchslochwelle_data(url_water_runoff,
                                                         time_interval)
        return water_runoff_data

    def get_fuchslochwelle_data(self, url, time_interval):
        page = urlopen(url)
        html_bytes = page.read()
        html = html_bytes.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        fuchslochwelle_data_arr = soup.find_all("tr", class_="row")

        data = {}
        for fuchslochwelle_data in fuchslochwelle_data_arr:
            fuchslochwelle_data = fuchslochwelle_data.find_all("td")
            time = fuchslochwelle_data[0].get_text()
            value = fuchslochwelle_data[1].get_text()
            value = tranform_values(value)

            time_parsed = get_datetime_obj_from_db_time_str(time)

            if (get_time_difference(TIME_NOW, time_parsed) <
                    time_interval):
                data[time] = value

        return data

class ThunStatDb(RiverwaveStatDb):

    def __init__(self, region='eu-central-1', stage='dev'):
        super().__init__(riverwave_name="thun", region=region, stage=stage)

    def get_data_water_level(self, time_interval=DEF_TIME_INTERVAL):
        url_water_lvl = "https://www.hydrodaten.admin.ch/lhg/az/dwh/csv/BAFU_2030_PegelRadar.csv"
        water_lvl_data = self.get_thun_data(url_water_lvl, time_interval)
        return water_lvl_data

    def get_data_water_temperature(self, time_interval=DEF_TIME_INTERVAL):
        url_water_temperature = "https://www.hydrodaten.admin.ch/lhg/az/dwh/csv/BAFU_2030_Wassertemperatur.csv"
        water_temperature_data = self.get_thun_data(url_water_temperature, time_interval)
        return water_temperature_data

    def get_data_water_runoff(self, time_interval=DEF_TIME_INTERVAL):
        url_water_runoff = "https://www.hydrodaten.admin.ch/lhg/az/dwh/csv/BAFU_2030_AbflussRadar.csv"
        water_runoff_data = self.get_thun_data(url_water_runoff, time_interval)
        return water_runoff_data

    def get_thun_data(self, url, time_interval):

        page = urlopen(url)
        html_bytes = page.read()
        html = html_bytes.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        body = soup.get_text()
        data = {}

        csv_file = open("/tmp/data.csv", "w")
        csv_file.write(body)
        csv_file.close()

        with open('/tmp/data.csv', 'r') as csv_file:

            reader = csv.reader(csv_file)
            next(reader)

            for row in reader:

                time_parsed = transform_swiss_time(row[0])
                time = get_db_time_str_from_datetime_obj(time_parsed)

                value = round(float(row[1]), 1)
                value = tranform_values(value)

                if (get_time_difference(TIME_NOW, time_parsed) <
                        time_interval):
                    data[time] = value

        os.remove("/tmp/data.csv")
        return data


class BremgartenStatDb(RiverwaveStatDb):

    def __init__(self, region='eu-central-1', stage='dev'):
        super().__init__(riverwave_name="bremgarten", region=region, stage=stage)

    def get_data_water_level(self, time_interval=DEF_TIME_INTERVAL):
        url_water_lvl = "https://www.hydrodaten.admin.ch/lhg/az/dwh/csv/BAFU_2018_PegelPneumatik.csv"
        water_lvl_data = self.get_bremgarten_data(url_water_lvl, time_interval)
        return water_lvl_data

    def get_data_water_temperature(self, time_interval=DEF_TIME_INTERVAL):
        url_water_temperature = "https://www.hydrodaten.admin.ch/lhg/az/dwh/csv/BAFU_2018_Wassertemperatur1.csv"
        water_temperature_data = self.get_bremgarten_data(url_water_temperature, time_interval)
        return water_temperature_data

    def get_data_water_runoff(self, time_interval=DEF_TIME_INTERVAL):
        url_water_runoff = "https://www.hydrodaten.admin.ch/lhg/az/dwh/csv/BAFU_2018_AbflussPneumatik.csv"
        water_runoff_data = self.get_bremgarten_data(url_water_runoff, time_interval)
        return water_runoff_data

    def get_bremgarten_data(self, url, time_interval):

        page = urlopen(url)
        html_bytes = page.read()
        html = html_bytes.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        body = soup.get_text()
        data = {}

        csv_file = open("/tmp/data.csv", "w")
        csv_file.write(body)
        csv_file.close()

        with open('/tmp/data.csv', 'r') as csv_file:

            reader = csv.reader(csv_file)
            next(reader)

            for row in reader:

                time_parsed = transform_swiss_time(row[0])
                time = get_db_time_str_from_datetime_obj(time_parsed)

                value = round(float(row[1]), 1)
                value = tranform_values(value)

                if (get_time_difference(TIME_NOW, time_parsed) <
                        time_interval):
                    data[time] = value

        os.remove("/tmp/data.csv")
        return data
