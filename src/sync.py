from src.riverwave_stat import (
    EisbachStatDb,
    TheRiverwaveStatDb,
    FuchslochwelleStatDb,
    ThunStatDb,
    BremgartenStatDb
)
import os


def sync(event, context):
    region = os.getenv("REGION")
    stage = os.getenv("STAGE")

    try:
        print("Start Sync Eisbach")
        e1 = EisbachStatDb(region=region, stage=stage)
        e1.write_data()
        print("Finish Sync Eisbach")
    except:
        print("Failed Sync Eisbach")

    try:
        print("Start Sync THE.RIVERWAVE")
        tr = TheRiverwaveStatDb(region=region, stage=stage)
        tr.write_data()
        print("Finish Sync THE.RIVERWAVE")
    except:
        print("Failed Sync THE.RIVERWAVE")

    try:
        print("Start Sync Fuchslochwelle")
        flw = FuchslochwelleStatDb(region=region, stage=stage)
        flw.write_data()
        print("Finish Sync Fuchslochwelle")
    except:
        print("Failed Sync Fuchslochwelle")

    try:
        print("Start Sync Thun")
        thn = ThunStatDb(region=region, stage=stage)
        thn.write_data()
        print("Finish Sync Thun")
    except:
        print("Failed Sync Thun")

    try:
        print("Start Sync Bremgarten")
        bg = BremgartenStatDb(region=region, stage=stage)
        bg.write_data()
        print("Finish Sync Bremgarten")
    except:
        print("Failed Sync Bremgarten")