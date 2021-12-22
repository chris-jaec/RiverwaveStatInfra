from src.riverwave_stat import EisbachStatDb, AlmkanalStatDb, TheRiverwaveStatDb, FuchslochwelleStatDb
import os


def sync(event, context):
    region = os.getenv("REGION")
    stage = os.getenv("STAGE")

    print("Start Sync Eisbach")
    e1 = EisbachStatDb(region=region, stage=stage)
    e1.write_data()
    print("Finish Sync Eisbach")

    print("Start Sync THE.RIVERWAVE")
    tr = TheRiverwaveStatDb(region=region, stage=stage)
    tr.write_data()
    print("Finish Sync THE.RIVERWAVE")

    print("Start Sync Almkanal")
    ak = AlmkanalStatDb(region=region, stage=stage)
    ak.write_data()
    print("Finish Sync Almkanal")

    print("Start Sync Fuchslochwelle")
    flw = FuchslochwelleStatDb(region=region, stage=stage)
    flw.write_data()
    print("Finish Sync Fuchslochwelle")
