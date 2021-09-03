from src.riverwave_stat import EisbachStatDb, AlmkanalStatDb, EbenseeStatDb
import os


def sync(event, context):
    region = os.getenv("REGION")
    stage = os.getenv("STAGE")

    print("Start Sync Eisbach")
    e1 = EisbachStatDb(region=region, stage=stage)
    e1.update_last_entries()
    print("Finish Sync Eisbach")

    print("Start Sync Almkanal")
    ak = AlmkanalStatDb(region=region, stage=stage)
    ak.update_last_entries()
    print("Finish Sync Almkanal")

    print("Start Sync Ebensee")
    es = EbenseeStatDb(region=region, stage=stage)
    es.update_last_entries()
    print("Finish Sync Ebensee")
