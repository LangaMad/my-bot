from aiogram import Router, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message, CallbackQuery, FSInputFile
from .keyboards import *
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

@router.message(Command('start'))
async def start_command(message: Message):
    await message.answer(
        f"""Привет, {message.from_user.first_name}
        я бот для продажи видео игр помогу и подскажу тебе в поиске!""",
        reply_markup=kb,
    )

@router.message(Command('help'))
async def help_command(message: Message):
    await message.answer("Если нужна помощь по товарам\n Позвони по номеру: 0556767676")

@router.message(F.text.lower() == 'hello')
async def hello_command(message: Message):
    await message.answer("Hello! How are you?")

@router.message(F.text == 'Категории')
async def category_command(message: Message):
    await message.answer("Выберите категорию", reply_markup=await categories())

@router.callback_query(F.data.startswith('category_'))
async def select_category(callback: CallbackQuery):
    await callback.message.delete()
    category_id = int(callback.data.split('_')[1])
    await callback.message.answer(
        text='Игры по этой категории',
        reply_markup=await games(category_id=category_id, page=1),
    )

@router.callback_query(F.data.startswith('page_'))
async def paginate_games(callback: CallbackQuery):
    data = callback.data.split('_')
    category_id = int(data[1])
    page = int(data[2])
    await callback.message.edit_reply_markup(
        reply_markup=await games(category_id=category_id, page=page)
    )




@router.callback_query(F.data.startswith('game_'))
async def select_game(callback: CallbackQuery):
    await callback.message.delete()
    game_id = int(callback.data.split('_')[1])
    game = await get_game(game_id)
    description = game.description

    if game.image.startswith('http') or game.image.startswith('AgAC'):
        # Использование file_id
        photo = game.image
    else:
        # Использование FSInputFile
        photo = FSInputFile(game.image)

    await callback.message.answer_photo(
        photo=photo,
        caption=f'{game.game_name} \n {description.capitalize().strip()} \n {game.price}$',
        reply_markup=await back_delete(game_id)
    )
    
@router.callback_query(F.data == 'back_to_categories')
async def back_to_categories(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        text='Выберите категорию',
        reply_markup=await categories(),
    )

@router.callback_query(F.data.startswith('delete_'))
async def delete_game2(callback: CallbackQuery):
    game_id = int(callback.data.split('_')[1])
    await delete_game(game_id)
    await callback.message.delete()
    await callback.answer('Game has been deleted',
                          reply_markup= await categories())
    

class AddGame(StatesGroup):
    game_name = State()
    description = State()
    price = State()
    image = State()
    category_id = State()

@router.message(Command('add_game'))
async def add_game(message: Message, state: FSMContext):
    await message.answer('Введите название игры')
    await state.set_state(AddGame.game_name)

@router.message(AddGame.game_name, StateFilter(AddGame))
async def enter_game_name(message: Message, state: FSMContext):
    await state.update_data(game_name=message.text)
    await message.answer('Введите описание игры')
    await state.set_state(AddGame.description)

@router.message(AddGame.description, StateFilter(AddGame))
async def enter_game_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer('Введите цену игры')
    await state.set_state(AddGame.price)

@router.message(AddGame.price, StateFilter(AddGame))
async def enter_game_price(message: Message, state: FSMContext):
    await state.update_data(price=int(message.text))
    await message.answer('Отправьте фото игры')
    await state.set_state(AddGame.image)

@router.message(AddGame.image, StateFilter(AddGame))
async def enter_game_image(message: Message, state: FSMContext):
    await state.update_data(image=message.photo[0].file_id)
    await message.answer('Выберите категорию', reply_markup=await categories2())
    await state.set_state(AddGame.category_id)

@router.callback_query(AddGame.category_id, StateFilter(AddGame))
async def enter_game_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split('_')[1])
    data = await state.get_data()
    game = Game(
        game_name=data['game_name'],
        description=data['description'],
        price=data['price'],
        image=data['image'],
        category_id=category_id,
    )
    await add_game2(game)
    await callback.answer('Game has been added successfully')
    await state.clear()
