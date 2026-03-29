from math import isinf, isnan

from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from cexprtk import evaluate_expression as evaluate

from common.rates import Data
from db import user_in_db, get_currency_pair, get_round_state

router = Router()

DEFAULT_FROM = "USD"
DEFAULT_TO = "GBP"


async def get_user_pair(user_id: int) -> tuple[str, str]:
    if await user_in_db(user_id):
        curr_from, curr_to = await get_currency_pair(user_id)
        return curr_from.split()[0], curr_to.split()[0]
    return DEFAULT_FROM, DEFAULT_TO


async def get_user_round(user_id: int) -> bool:
    if await user_in_db(user_id):
        return await get_round_state(user_id)
    return True


@router.inline_query()
async def inline_convert(query: InlineQuery):
    text = query.query.strip()
    user_id = query.from_user.id

    if not text:
        await query.answer([], cache_time=1)
        return

    try:
        value = float(evaluate(text.replace(",", ".").replace(" ", ""), {}))
    except Exception:
        await query.answer([], cache_time=1)
        return

    if isnan(value) or isinf(value):
        await query.answer([], cache_time=1)
        return

    curr_from, curr_to = await get_user_pair(user_id)

    if curr_from not in Data.rates or curr_to not in Data.rates:
        await query.answer([], cache_time=1)
        return

    rate = Data.rates[curr_to] / Data.rates[curr_from]
    result = value * rate

    round_result = await get_user_round(user_id)
    if round_result:
        value = round(value, 2)
        result = round(result, 2)

    from common.currencies import CURRENCIES
    from_flag = CURRENCIES.get(curr_from, "")
    to_flag = CURRENCIES.get(curr_to, "")

    text_result = f"{value} {curr_from} {from_flag}  =  {result} {curr_to} {to_flag}"

    await query.answer(
        results=[
            InlineQueryResultArticle(
                id="1",
                title=text_result,
                input_message_content=InputTextMessageContent(
                    message_text=text_result
                ),
            )
        ],
        cache_time=30,
    )
