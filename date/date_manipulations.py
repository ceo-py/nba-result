import datetime


# async def get_current_date() -> str:
#     return datetime.date.today()

async def get_current_date() -> str:
    return datetime.date.today() - datetime.timedelta(days=1)


async def get_previous_date(current_date: str) -> datetime:
    return current_date - datetime.timedelta(days=1)


async def convert_data_time(data_to_convert: datetime) -> str:
    return (
        f"{data_to_convert.strftime('%b')}+{data_to_convert.day}+{data_to_convert.year}"
    )
