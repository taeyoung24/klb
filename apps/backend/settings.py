import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_URL                = os.getenv('API_URL', 'http://localhost:3000')
DATABASE_URL           = os.environ['DATABASE_URL']

DISCORD_LOG_WH_URL     = os.environ['DISCORD_LOG_WH_URL']
DISCORD_REPORT_WH_URL  = os.environ['DISCORD_REPORT_WH_URL']

OPENROUTER_API_KEY     = os.environ['OPENROUTER_API_KEY']


class CONFIG:
    version = "1.0.0"
    base_datetime = datetime(2026, 1, 1, 0, 0, 0)
    simulation_version = "0.1.0"


class DISCORD_CONSTANTS:
    client_id = 875972355061604415

    # roles
    ceo_role_id       = 779232705749450757
    operator_role_id  = 1278242616411947019
    staff_role_id     = 1278242945191116833
    guest_role_id     = 1278243280429125675

    # users
    ahngebi_user_id   = 334298300364619776
    new_user_id       = 375933100867321856

    # channels
    report_channel_id = 1278251318485450752
    log_channel_id = 1278248328093499435
    botcommands_channel_id = 1278252356814766100
    schedules_channel_id = 1278255266638463030
    schedules_alarm_channel_id = 1315844534021914754
    schedule_evaluate_channel_id = 1278294428372570172
    threadoc_channel_id = 1316746136463216660
    record_channel_id = 1278249055629348905
    ceo_channel_id = 1278246204022587438
    diogg_flb_channel_id = 1404112833280741539
    ui_channel_id = 1489958734494175302
    ts_channel_ids: list[int] = []

    # guilds
    ahngebi_guild_id = 1087312437885292554
    di_space_guild_id = 779231268683776030

