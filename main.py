import asyncio
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from pyflipper.pyflipper import PyFlipper

from config import BOT_TOKEN, COM_PORT
from flipperInterface import get_device_name, get_list_of_ir, get_ir_file_data, decode_ir_file, send_ir_command


def create_keyboard(options):
    """Функция для создания клавиатуры из списка возможных вариантов"""
    return types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text=f"{elem}")] for elem in options])


class CurrentState(StatesGroup):
    start = State()
    selection_remote = State()
    selection_command = State()


async def get_flipper():
    """Асинхронный контекст для работы с Flipper"""
    try:
        flipper = PyFlipper(com=COM_PORT)
        return flipper
    except Exception as e:
        print(f"Ошибка при подключении к Flipper: {e}")
        return None


router = Router()

@router.message(CurrentState.start)
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    flipper = await get_flipper()
    if flipper:
        await message.answer(
            f"Привет, я бот для управления IR устройствами через FlipperZero *{get_device_name(flipper)}*."
            f"\nВыбери нужный тебе пульт.",
            reply_markup=create_keyboard(get_list_of_ir(flipper)),
            parse_mode="Markdown"
        )
        await state.set_state(CurrentState.selection_remote)
    else:
        await message.answer("Не удалось подключиться к Flipper. Попробуйте позже.")


@router.message(CurrentState.selection_remote)
async def cmd_select_ir(message: types.Message, state: FSMContext):
    flipper = await get_flipper()
    if flipper:
        available_remotes = get_list_of_ir(flipper)
        if message.text in available_remotes:
            ir_data = get_ir_file_data(flipper, message.text)
            if ir_data:
                currentIR = decode_ir_file(ir_data)
                await state.update_data(currentIR=currentIR)
                await state.set_state(CurrentState.selection_command)
                await message.answer(
                    "Вот доступные команды, выбери нужную тебе",
                    reply_markup=create_keyboard(list(currentIR.keys()) + ["Назад"])
                )
            else:
                await message.answer("Не удалось найти файл IR. Попробуйте другой пульт.")
        else:
            await message.answer("Неправильный выбор пульта. Попробуйте снова.")
    else:
        await message.answer("Не удалось подключиться к Flipper.")


@router.message(CurrentState.selection_command)
async def cmd_select_command(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.set_state(CurrentState.start)
        await cmd_start(message, state)
    else:
        data = await state.get_data()
        flipper = await get_flipper()
        if flipper and message.text in data["currentIR"]:
            send_ir_command(flipper, data["currentIR"], message.text)
            await message.answer("Команда выполнена!")
        else:
            await message.answer("Ошибка: команда не распознана или Flipper недоступен.")


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
