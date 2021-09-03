import json
from datetime import datetime
from urllib.request import urlopen

import boto3
from bs4 import BeautifulSoup

from src.utils import (
    get_db_time_str_from_datetime_obj,
    get_datetime_obj_from_db_time_str,
    get_time_difference,
    transform_ebensee_time
)

TIME_NOW = datetime.now()


class RiverwaveStatDb(object):

    def __init__(self, riverwave_name, region='eu-central-1', stage='dev'):
        dynamodb = boto3.resource('dynamodb', region_name=region)
        self.database = dynamodb.Table(
            f'riverwavestat-{stage}-{riverwave_name}')

    def update_statistic(self, datetime, water_level, water_temp,
                         water_runoff):
        response = self.database.put_item(
            Item={
                'datetime': str(datetime),
                'water_level': str(water_level),
                'water_temp': str(water_temp),
                'water_runoff': str(water_runoff)
            }
        )

    def fetch_latest_statistics(self, amount=5):
        pass

    def update_last_entries(self):
        latest_statistics = self.fetch_latest_statistics()

        for entry in latest_statistics:
            self.update_statistic(entry["datetime"], entry["water_level"],
                                  entry["water_temp"], entry["water_runoff"])


class EisbachStatDb(RiverwaveStatDb):

    def __init__(self, region='eu-central-1', stage='dev'):
        super().__init__(riverwave_name="eisbach", region=region, stage=stage)

    def fetch_latest_statistics(self, time_interval=180):
        url_water_lvl = "https://www.hnd.bayern.de/pegel/donau_bis_kelheim/muenchen-himmelreichbruecke-16515005/tabelle?methode=wasserstand&setdiskr=15"
        url_water_runoff = "https://www.hnd.bayern.de/pegel/donau_bis_kelheim/muenchen-himmelreichbruecke-16515005/tabelle?methode=abfluss&setdiskr=15"
        url_water_temp = "https://www.gkd.bayern.de/de/fluesse/wassertemperatur/kelheim/muenchen-himmelreichbruecke-16515005/messwerte/tabelle"

        water_lvl_data = self.get_eisbach_data(url_water_lvl, time_interval)
        water_runoff_data = self.get_eisbach_data(url_water_runoff,
                                                  time_interval)
        water_temp_data = self.get_eisbach_data(url_water_temp, time_interval)

        all_times = sorted(
            set(
                list(water_lvl_data.keys()) +
                list(water_temp_data.keys()) +
                list(water_runoff_data.keys())
            )
        )

        statistics = []

        for time in all_times:
            stat_dict = {}
            stat_dict["datetime"] = time
            stat_dict["water_level"] = water_lvl_data.get(time)
            stat_dict["water_temp"] = water_temp_data.get(time)
            stat_dict["water_runoff"] = water_runoff_data.get(time)

            if not stat_dict["water_temp"] == "--":
                statistics.append(stat_dict)

        return statistics

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

            time_parsed = get_datetime_obj_from_db_time_str(time)

            if (get_time_difference(TIME_NOW, time_parsed) <
                    time_interval):
                data[time] = value

        return data


class AlmkanalStatDb(RiverwaveStatDb):

    def __init__(self, region='eu-central-1', stage='dev'):
        super().__init__(riverwave_name="almkanal", region=region, stage=stage)

    def fetch_latest_statistics(self, time_interval=120):
        url_water_lvl = "https://www.hnd.bayern.de/pegel/inn/salzburg-mayburger-kai-18601505/tabelle?methode=wasserstand&setdiskr=15"

        water_lvl_data = self.get_almkanal_data(url_water_lvl, time_interval)

        all_times = (water_lvl_data.keys())

        statistics = []

        for time in all_times:
            stat_dict = {}
            stat_dict["datetime"] = time
            stat_dict["water_level"] = water_lvl_data.get(time)
            stat_dict["water_temp"] = None
            stat_dict["water_runoff"] = None
            statistics.append(stat_dict)

        return statistics

    def get_almkanal_data(self, url, time_interval):
        page = urlopen(url)
        html_bytes = page.read()
        html = html_bytes.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        almkanal_data_arr = soup.find_all("tr", class_="row")

        data = {}
        for almkanal_data in almkanal_data_arr:
            almkanal_data = almkanal_data.find_all("td")
            time = almkanal_data[0].get_text()
            value = almkanal_data[1].get_text()

            time_parsed = get_datetime_obj_from_db_time_str(time)

            if (get_time_difference(TIME_NOW, time_parsed) <
                    time_interval):
                data[time] = value

        return data


class EbenseeStatDb(RiverwaveStatDb):

    def __init__(self, region='eu-central-1', stage='dev'):
        super().__init__(riverwave_name="ebensee", region=region, stage=stage)

    def fetch_latest_statistics(self, time_interval=120):
        url_water_lvl = "https://hydro.ooe.gv.at/data/internet/stations/OG/4470/S/week.json"
        url_water_temp = "https://hydro.ooe.gv.at/data/internet/stations/OG/4470/WT/week.json"

        water_lvl_data = self.get_ebensee_data(url_water_lvl, time_interval)
        water_temp_data = self.get_ebensee_data(url_water_temp, time_interval)

        all_times = sorted(
            set(
                list(water_lvl_data.keys()) +
                list(water_temp_data.keys())
            )
        )

        statistics = []

        for time in all_times:
            stat_dict = {}
            stat_dict["datetime"] = time
            stat_dict["water_level"] = water_lvl_data.get(time)
            stat_dict["water_temp"] = water_temp_data.get(time)
            stat_dict["water_runoff"] = None
            statistics.append(stat_dict)

        return statistics

    def get_ebensee_data(self, url, time_interval):
        page = urlopen(url)
        html_bytes = page.read()
        html = html_bytes.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        body = soup.get_text()

        ebensee_data_arr = json.loads(body)[0]['data']
        ebensee_data_arr.reverse()

        data = {}
        for ebensee_data in ebensee_data_arr:
            time_parsed = transform_ebensee_time(ebensee_data[0])
            time = get_db_time_str_from_datetime_obj(time_parsed)
            value = ebensee_data[1]

            if (get_time_difference(TIME_NOW, time_parsed) <
                    time_interval):
                data[time] = value

        return data
