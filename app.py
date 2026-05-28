import streamlit as st
import psycopg2
import pandas as pd
import base64
import os
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    icon_path = os.path.join(BASE_DIR, "icon.png")
    icon_image = Image.open(icon_path)
except FileNotFoundError:
    icon_image = "🔥"

st.set_page_config(
    page_title="База данных Dark Souls",
    page_icon=icon_image,
    layout="wide"
)


# --- НАСТРОЙКА ФОНА И МУЗЫКИ ---
def get_base64_of_local_file(file_name):
    file_path = os.path.join(BASE_DIR, file_name)
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


try:
    bin_str = get_base64_of_local_file("background.png")
    page_bg_img = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    [data-testid="stHeader"] {{
        background: rgba(0,0,0,0);
    }}
    [data-testid="stSidebar"] {{
        background-color: rgba(20, 20, 20, 0.85) !important;
    }}
    .stTabs button {{
        color: #fff !important;
    }}
    h1, h2, h3, p, span {{
        color: #e0e0e0 !important;
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)
except FileNotFoundError:
    st.sidebar.error(f"Файл 'background.png' не найден в {BASE_DIR}!")

try:
    audio_str = get_base64_of_local_file("theme.mp3")
    audio_html = f"""
    <div style="position: fixed; bottom: 15px; right: 15px; z-index: 99999; background: rgba(30,30,30,0.9); padding: 10px; border: 1px solid #ff4b4b; border-radius: 8px;">
        <span style="color: #ff4b4b; font-size: 13px; display: block; text-align: center; margin-bottom: 5px; font-weight: bold;">Звуковое сопровождение</span>
        <audio id="bg-audio" controls loop style="height: 30px; width: 220px;">
            <source src="data:audio/mp3;base64,{audio_str}" type="audio/mp3">
        </audio>
    </div>
    """
    st.markdown(audio_html, unsafe_allow_html=True)
except FileNotFoundError:
    st.sidebar.error(f"Файл 'theme.mp3' не найден в {BASE_DIR}!")

st.title("Панель управления базой данных Dark Souls")


# 1. Подключение к базе данных
@st.cache_resource
def init_connection():
    connection = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="000",
        port="5432"
    )
    connection.set_client_encoding('UTF8')
    return connection


try:
    conn = init_connection()
except Exception as e:
    st.error(f"Не удалось подключиться к базе данных: {e}")
    st.stop()

ITEM_TYPES = [
    "straight_swords", "greatswords", "ultra_greatswords", "daggers",
    "curved_swords", "katanas", "spears", "halberds", "axes", "maces",
    "staffs_sorcery", "pyromancy_flames", "talismans_miracles", "shields",
    "armor_pieces", "rings", "restorative_items", "keys", "boss_souls"
]


# 2. Функции для получения списков из базы
def get_locations():
    with conn.cursor() as cur:
        cur.execute('SELECT location_id, location_name FROM "DarkSouls".locations ORDER BY location_name;')
        return cur.fetchall()


def get_items():
    with conn.cursor() as cur:
        cur.execute('SELECT item_id, item_name FROM "DarkSouls".items ORDER BY item_name;')
        return cur.fetchall()


def get_enemies_all():
    with conn.cursor() as cur:
        cur.execute('SELECT enemy_id, enemy_name FROM "DarkSouls".enemies ORDER BY enemy_name;')
        return cur.fetchall()


def get_npcs_all():
    with conn.cursor() as cur:
        cur.execute('SELECT npc_id, npc_name FROM "DarkSouls".npc ORDER BY npc_name;')
        return cur.fetchall()


# Детальная информация для редактирования
def get_enemy_details(enemy_id):
    with conn.cursor() as cur:
        cur.execute('SELECT enemy_name, enemy_type, item_id FROM "DarkSouls".enemies WHERE enemy_id = %s;', (enemy_id,))
        return cur.fetchone()


def get_npc_details(npc_id):
    with conn.cursor() as cur:
        cur.execute('SELECT npc_name, npc_type, item_id FROM "DarkSouls".npc WHERE npc_id = %s;', (npc_id,))
        return cur.fetchone()


def get_item_details(item_id):
    with conn.cursor() as cur:
        cur.execute('SELECT item_name, item_description, item_type FROM "DarkSouls".items WHERE item_id = %s;',
                    (item_id,))
        return cur.fetchone()


# Функции получения текущего состава конкретной локации (для предзаполнения multiselect)
def get_current_enemies_for_location(location_id):
    with conn.cursor() as cur:
        cur.execute('SELECT enemy_id FROM "DarkSouls".enemies_locations WHERE location_id = %s;', (location_id,))
        return [row[0] for row in cur.fetchall()]


def get_current_npcs_for_location(location_id):
    with conn.cursor() as cur:
        cur.execute('SELECT npc_id FROM "DarkSouls".npcs_locations WHERE location_id = %s;', (location_id,))
        return [row[0] for row in cur.fetchall()]


def get_current_items_for_location(location_id):
    with conn.cursor() as cur:
        cur.execute('SELECT item_id FROM "DarkSouls".items_locations WHERE location_id = %s;', (location_id,))
        return [row[0] for row in cur.fetchall()]


# Обновляем словари
locations = get_locations()
location_dict = {name: idx for idx, name in locations}

items = get_items()
item_dict = {name: idx for idx, name in items}
item_id_to_name = {idx: name for idx, name in items}

enemies_all = get_enemies_all()
enemy_dict = {name: idx for idx, name in enemies_all}
enemy_id_to_name = {idx: name for idx, name in enemies_all}

npcs_all = get_npcs_all()
npc_dict = {name: idx for idx, name in npcs_all}
npc_id_to_name = {idx: name for idx, name in npcs_all}

# --- ИНТЕРФЕЙС ---

st.sidebar.header("Выбор локации")
if location_dict:
    selected_location_name = st.sidebar.selectbox("Выберите место на карте:", list(location_dict.keys()))
    selected_location_id = location_dict[selected_location_name]
else:
    st.sidebar.warning("В базе пока нет локаций. Сначала добавьте локацию.")
    selected_location_name = None
    selected_location_id = None

# Вкладки
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🔍 Просмотр",
    "➕ Добавить врага",
    "➕ Добавить NPC",
    "➕ Добавить локацию",
    "➕ Добавить предмет",
    "✏️ Изменение данных",
    "🗑️ Удаление данных"
])

# --- ВКЛАДКА 1: ПРОСМОТР ---
with tab1:
    if selected_location_name:
        st.header(f"Текущая локация: {selected_location_name}")

        col_left, col_mid, col_right = st.columns(3)

        with col_left:
            st.subheader("Враги и боссы:")
            query_enemies = """
                SELECT 
                    e.enemy_name AS "Имя врага", 
                    e.enemy_type AS "Тип", 
                    i.item_name AS "Предмет"
                FROM "DarkSouls".enemies_locations el
                JOIN "DarkSouls".enemies e ON el.enemy_id = e.enemy_id
                LEFT JOIN "DarkSouls".items i ON e.item_id = i.item_id
                WHERE el.location_id = %s;
            """
            with conn.cursor() as cur:
                cur.execute(query_enemies, (selected_location_id,))
                rows_e = cur.fetchall()
                cols_e = [desc[0] for desc in cur.description]
            df_enemies = pd.DataFrame(rows_e, columns=cols_e)

            if not df_enemies.empty:
                st.dataframe(df_enemies, use_container_width=True)
            else:
                st.info("В этой локации врагов нет.")

        with col_mid:
            st.subheader("Персонажи (NPC):")
            query_npcs = """
                SELECT 
                    n.npc_name AS "Имя NPC", 
                    n.npc_type AS "Роль / Функция", 
                    i.item_name AS "Связанный предмет"
                FROM "DarkSouls".npcs_locations nl
                JOIN "DarkSouls".npc n ON nl.npc_id = n.npc_id
                LEFT JOIN "DarkSouls".items i ON n.item_id = i.item_id
                WHERE nl.location_id = %s;
            """
            with conn.cursor() as cur:
                cur.execute(query_npcs, (selected_location_id,))
                rows_n = cur.fetchall()
                cols_n = [desc[0] for desc in cur.description]
            df_npcs = pd.DataFrame(rows_n, columns=cols_n)

            if not df_npcs.empty:
                st.dataframe(df_npcs, use_container_width=True)
            else:
                st.info("В этой локации персонажей нет.")

        with col_right:
            st.subheader("Найдено на локации:")
            query_loc_items = """
                SELECT 
                    i.item_name AS "Название предмета",
                    i.item_type AS "Тип",
                    i.item_description AS "Описание"
                FROM "DarkSouls".items_locations il
                JOIN "DarkSouls".items i ON il.item_id = i.item_id
                WHERE il.location_id = %s;
            """
            with conn.cursor() as cur:
                cur.execute(query_loc_items, (selected_location_id,))
                rows_li = cur.fetchall()
                cols_li = [desc[0] for desc in cur.description]
            df_loc_items = pd.DataFrame(rows_li, columns=cols_li)

            if not df_loc_items.empty:
                st.dataframe(df_loc_items, use_container_width=True)
            else:
                st.info("Здесь свободно лежащих предметов нет.")
    else:
        st.info("Создайте хотя бы одну локацию на вкладке №4.")

# --- ВКЛАДКА 2: ДОБАВЛЕНИЕ ВРАГОВ ---
with tab2:
    if selected_location_name:
        st.header("Добавить нового врага")
        st.write(f"Враг появится в локации: **{selected_location_name}**")

        st.markdown("---")
        st.subheader("Шаг 1. Выберите предмет, который выпадает из врага:")

        item_option = st.radio(
            "Варианты:",
            ["Ничего не выпадает", "Выбрать уже существующий предмет", "Создать абсолютно новый предмет"],
            key="enemy_item_radio"
        )

        existing_item_id = None
        new_item_name = ""
        new_item_type = "unknown"
        new_item_desc = "unknown"

        if item_option == "Выбрать уже существующий предмет":
            if item_dict:
                chosen_item_name = st.selectbox("Выберите предмет из списка:", list(item_dict.keys()),
                                                key="enemy_item_select")
                existing_item_id = item_dict[chosen_item_name]
            else:
                st.warning("В базе нет предметов. Выберите вариант 'Создать абсолютно новый предмет'.")
                item_option = "Ничего не выпадает"

        elif item_option == "Создать абсолютно новый предмет":
            col1, col2 = st.columns(2)
            with col1:
                new_item_name = st.text_input("Название предмета:")
            with col2:
                new_item_type = st.selectbox("Категория предмета:", ITEM_TYPES, key="enemy_new_item_type_sb")
            new_item_desc = st.text_area("Описание предмета:", "Описание...")

        st.markdown("---")
        st.subheader("Шаг 2. Заполните данные врага:")

        with st.form("add_enemy_core_form"):
            enemy_name = st.text_input("Имя врага:")
            enemy_type = st.selectbox("Сложность врага:", ["ordinary_opponent", "unordinary_opponent", "boss"])

            submitted = st.form_submit_button("Сохранить врага")

            if submitted:
                if not enemy_name:
                    st.error("Введите имя врага!")
                else:
                    try:
                        with conn.cursor() as cur:
                            final_item_id = None

                            if item_option == "Создать абсолютно новый предмет":
                                if not new_item_name:
                                    st.error("Вы не указали название нового предмета!")
                                    st.stop()

                                cur.execute(
                                    'INSERT INTO "DarkSouls".items (item_name, item_description, item_type) VALUES (%s, %s, %s) RETURNING item_id;',
                                    (new_item_name, new_item_desc, new_item_type)
                                )
                                final_item_id = cur.fetchone()[0]

                            elif item_option == "Выбрать уже существующий предмет":
                                final_item_id = existing_item_id

                            cur.execute(
                                'INSERT INTO "DarkSouls".enemies (enemy_name, enemy_type, item_id) VALUES (%s, %s, %s) RETURNING enemy_id;',
                                (enemy_name, enemy_type, final_item_id)
                            )
                            new_enemy_id = cur.fetchone()[0]

                            cur.execute(
                                'INSERT INTO "DarkSouls".enemies_locations (enemy_id, location_id) VALUES (%s, %s);',
                                (new_enemy_id, selected_location_id)
                            )

                            conn.commit()
                            st.success(f"Враг {enemy_name} успешно сохранен!")
                            st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Ошибка сохранения: {e}")
    else:
        st.info("Сначала нужно добавить хотя бы одну локацию.")

# --- ВКЛАДКА 3: ДОБАВЛЕНИЕ NPC ---
with tab3:
    if selected_location_name:
        st.header("Добавить нового персонажа (NPC)")
        st.write(f"Персонаж появится в локации: **{selected_location_name}**")

        st.markdown("---")
        st.subheader("Шаг 1. Выберите предмет персонажа:")

        npc_item_option = st.radio(
            "Варианты:",
            ["Нет предмета", "Выбрать уже существующий предмет", "Создать абсолютно новый предмет"],
            key="npc_item_radio"
        )

        npc_existing_item_id = None
        npc_new_item_name = ""
        npc_new_item_type = "unknown"
        npc_new_item_desc = "unknown"

        if npc_item_option == "Выбрать уже существующий предмет":
            if item_dict:
                chosen_npc_item = st.selectbox("Выберите предмет из списка:", list(item_dict.keys()),
                                               key="npc_item_select")
                npc_existing_item_id = item_dict[chosen_npc_item]
            else:
                st.warning("В базе нет предметов. Выберите вариант 'Создать абсолютно новый предмет'.")
                npc_item_option = "Нет предмета"

        elif npc_item_option == "Создать абсолютно новый предмет":
            col1, col2 = st.columns(2)
            with col1:
                npc_new_item_name = st.text_input("Название предмета:", key="npc_item_name_input")
            with col2:
                npc_new_item_type = st.selectbox("Категория предмета:", ITEM_TYPES, key="npc_item_type_select")
            npc_new_item_desc = st.text_area("Описание предмета:", "Описание...", key="npc_item_desc_input")

        st.markdown("---")
        st.subheader("Шаг 2. Заполните данные персонажа:")

        with st.form("add_npc_core_form"):
            npc_name = st.text_input("Имя персонажа:")
            npc_role = st.text_input("Роль (например: Торговец, Кузнец, Учитель):")

            npc_submitted = st.form_submit_button("Сохранить персонажа")

            if npc_submitted:
                if not npc_name:
                    st.error("Введите имя персонажа!")
                else:
                    try:
                        with conn.cursor() as cur:
                            final_npc_item_id = None

                            if npc_item_option == "Создать абсолютно новый предмет":
                                if not npc_new_item_name:
                                    st.error("Вы не указали название нового предмета!")
                                    st.stop()

                                cur.execute(
                                    'INSERT INTO "DarkSouls".items (item_name, item_description, item_type) VALUES (%s, %s, %s) RETURNING item_id;',
                                    (npc_new_item_name, npc_new_item_desc, npc_new_item_type)
                                )
                                final_npc_item_id = cur.fetchone()[0]

                            elif npc_item_option == "Выбрать уже существующий предмет":
                                final_npc_item_id = npc_existing_item_id

                            cur.execute(
                                'INSERT INTO "DarkSouls".npc (npc_name, npc_type, item_id) VALUES (%s, %s, %s) RETURNING npc_id;',
                                (npc_name, npc_role, final_npc_item_id)
                            )
                            new_npc_id = cur.fetchone()[0]

                            cur.execute(
                                'INSERT INTO "DarkSouls".npcs_locations (npc_id, location_id) VALUES (%s, %s);',
                                (new_npc_id, selected_location_id)
                            )

                            conn.commit()
                            st.success(f"Персонаж {npc_name} успешно добавлен!")
                            st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Ошибка сохранения: {e}")
    else:
        st.info("Сначала нужно добавить хотя бы одну локацию.")

# --- ВКЛАДКА 4: ДОБАВЛЕНИЕ ЛОКАЦИЙ ---
with tab4:
    st.header("Добавить новую локацию")

    with st.form("add_location_form"):
        new_location_name = st.text_input("Название локации:")

        location_submitted = st.form_submit_button("Сохранить локацию")

        if location_submitted:
            if not new_location_name:
                st.error("Название не может быть пустым!")
            else:
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            'INSERT INTO "DarkSouls".locations (location_name) VALUES (%s) RETURNING location_id;',
                            (new_location_name,)
                        )
                        new_loc_id = cur.fetchone()[0]

                        conn.commit()
                        st.success(f"Локация {new_location_name} успешно создана!")
                        st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"Ошибка сохранения: {e}")

# --- ВКЛАДКА 5: ДОБАВЛЕНИЕ ЧИСТЫХ ПРЕДМЕТОВ ---
with tab5:
    st.header("Добавить новый предмет")
    st.write("Создайте предмет, чтобы затем использовать его в предметах локаций или выпадении с боссов.")

    with st.form("add_standalone_item_form"):
        st_item_name = st.text_input("Название предмета:")
        st_item_type = st.selectbox("Категория предмета:", ITEM_TYPES)
        st_item_desc = st.text_area("Описание предмета / Лор:", "Описание...")

        st_item_submitted = st.form_submit_button("Создать предмет")

        if st_item_submitted:
            if not st_item_name:
                st.error("Укажите название предмета!")
            else:
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            'INSERT INTO "DarkSouls".items (item_name, item_description, item_type) VALUES (%s, %s, %s);',
                            (st_item_name, st_item_desc, st_item_type)
                        )
                        conn.commit()
                        st.success(f"Предмет '{st_item_name}' успешно зарегистрирован!")
                        st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"Ошибка сохранения: {e}")

# --- ВКЛАДКА 6: ИЗМЕНЕНИЕ ДАННЫХ ---
with tab6:
    st.header("Редактирование существующих данных")
    st.write("Выберите категорию и объект, который хотите изменить:")

    category = st.selectbox("Что редактируем?", ["Врага / Босса", "Персонажа (NPC)", "Предмет", "Локацию"])
    st.markdown("---")

    if category == "Врага / Босса":
        if enemy_dict:
            enemy_to_edit_name = st.selectbox("Выберите врага для изменения:", list(enemy_dict.keys()),
                                              key="edit_enemy_select")
            enemy_to_edit_id = enemy_dict[enemy_to_edit_name]

            cur_name, cur_type, cur_item_id = get_enemy_details(enemy_to_edit_id)

            with st.form("edit_enemy_form"):
                new_name = st.text_input("Новое имя врага:", value=cur_name)
                type_options = ["ordinary_opponent", "unordinary_opponent", "boss"]
                try:
                    type_idx = type_options.index(cur_type)
                except ValueError:
                    type_idx = 0
                new_type = st.selectbox("Новая сложность:", type_options, index=type_idx)

                item_options_list = ["Нет предмета"] + list(item_dict.keys())
                cur_item_name = item_id_to_name.get(cur_item_id, "Нет предмета")
                try:
                    item_idx = item_options_list.index(cur_item_name)
                except ValueError:
                    item_idx = 0

                new_item_chosen = st.selectbox("Изменить выпадающий предмет:", item_options_list, index=item_idx)

                save_enemy = st.form_submit_button("Сохранить изменения")
                if save_enemy:
                    if not new_name:
                        st.error("Имя не может быть пустым!")
                    else:
                        try:
                            final_item_id = None if new_item_chosen == "Нет предмета" else item_dict[new_item_chosen]
                            with conn.cursor() as cur:
                                cur.execute(
                                    'UPDATE "DarkSouls".enemies SET enemy_name = %s, enemy_type = %s, item_id = %s WHERE enemy_id = %s;',
                                    (new_name, new_type, final_item_id, enemy_to_edit_id)
                                )
                                conn.commit()
                            st.success(f"Данные врага '{new_name}' успешно обновлены!")
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Ошибка изменения: {e}")
        else:
            st.info("В базе нет врагов для редактирования.")

    elif category == "Персонажа (NPC)":
        if npc_dict:
            npc_to_edit_name = st.selectbox("Выберите NPC для изменения:", list(npc_dict.keys()), key="edit_npc_select")
            npc_to_edit_id = npc_dict[npc_to_edit_name]

            cur_name, cur_role, cur_item_id = get_npc_details(npc_to_edit_id)

            with st.form("edit_npc_form"):
                new_name = st.text_input("Новое имя персонажа:", value=cur_name)
                new_role = st.text_input("Новая роль / функция:", value=cur_role)

                item_options_list = ["Нет предмета"] + list(item_dict.keys())
                cur_item_name = item_id_to_name.get(cur_item_id, "Нет предмета")
                try:
                    item_idx = item_options_list.index(cur_item_name)
                except ValueError:
                    item_idx = 0
                new_item_chosen = st.selectbox("Изменить связанный предмет:", item_options_list, index=item_idx)

                save_npc = st.form_submit_button("Сохранить изменения")
                if save_npc:
                    if not new_name:
                        st.error("Имя не может быть пустым!")
                    else:
                        try:
                            final_item_id = None if new_item_chosen == "Нет предмета" else item_dict[new_item_chosen]
                            with conn.cursor() as cur:
                                cur.execute(
                                    'UPDATE "DarkSouls".npc SET npc_name = %s, npc_type = %s, item_id = %s WHERE npc_id = %s;',
                                    (new_name, new_role, final_item_id, npc_to_edit_id)
                                )
                                conn.commit()
                            st.success(f"Данные персонажа '{new_name}' успешно обновлены!")
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Ошибка изменения: {e}")
        else:
            st.info("В базе нет персонажей для редактирования.")

    elif category == "Предмет":
        if item_dict:
            item_to_edit_name = st.selectbox("Выберите предмет для изменения:", list(item_dict.keys()),
                                             key="edit_item_select")
            item_to_edit_id = item_dict[item_to_edit_name]

            cur_name, cur_desc, cur_type = get_item_details(item_to_edit_id)

            with st.form("edit_item_form"):
                new_name = st.text_input("Новое название предмета:", value=cur_name)

                type_options = ITEM_TYPES + ["unknown"]
                try:
                    type_idx = type_options.index(cur_type)
                except ValueError:
                    type_idx = len(type_options) - 1
                new_type = st.selectbox("Новый тип предмета:", type_options, index=type_idx)
                new_desc = st.text_area("Новое описание:", value=cur_desc)

                save_item = st.form_submit_button("Сохранить изменения")
                if save_item:
                    if not new_name:
                        st.error("Название предмета не может быть пустым!")
                    else:
                        try:
                            with conn.cursor() as cur:
                                cur.execute(
                                    'UPDATE "DarkSouls".items SET item_name = %s, item_description = %s, item_type = %s WHERE item_id = %s;',
                                    (new_name, new_desc, new_type, item_to_edit_id)
                                )
                                conn.commit()
                            st.success(f"Предмет '{new_name}' изменен!")
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Ошибка изменения: {e}")
        else:
            st.info("В базе нет предметов для редактирования.")

    elif category == "Локацию":
        if location_dict:
            loc_to_edit_name = st.selectbox("Выберите локацию для изменения:", list(location_dict.keys()),
                                            key="edit_loc_select")
            loc_to_edit_id = location_dict[loc_to_edit_name]

            curr_enemies_ids = get_current_enemies_for_location(loc_to_edit_id)
            curr_npcs_ids = get_current_npcs_for_location(loc_to_edit_id)
            curr_items_ids = get_current_items_for_location(loc_to_edit_id)

            curr_enemies_names = [enemy_id_to_name[eid] for eid in curr_enemies_ids if eid in enemy_id_to_name]
            curr_npcs_names = [npc_id_to_name[nid] for nid in curr_npcs_ids if nid in npc_id_to_name]
            curr_items_names = [item_id_to_name[iid] for iid in curr_items_ids if iid in item_id_to_name]

            with st.form("edit_loc_full_form"):
                new_name = st.text_input("Новое название локации:", value=loc_to_edit_name)

                st.markdown("---")
                st.markdown("##### Настроить врагов на локации:")
                updated_enemies = st.multiselect(
                    "Выберите врагов, которые обитают здесь:",
                    options=list(enemy_dict.keys()),
                    default=curr_enemies_names
                )

                st.markdown("##### Настроить персонажей (NPC) на локации:")
                updated_npcs = st.multiselect(
                    "Выберите NPC, которые стоят здесь:",
                    options=list(npc_dict.keys()),
                    default=curr_npcs_names
                )

                st.markdown("##### Настроить лежащие предметы на локации:")
                updated_items = st.multiselect(
                    "Выберите предметы, которые лежат на земле/в сундуках:",
                    options=list(item_dict.keys()),
                    default=curr_items_names
                )

                save_loc = st.form_submit_button("Сохранить изменения локации")
                if save_loc:
                    if not new_name:
                        st.error("Название локации не может быть пустым!")
                    else:
                        try:
                            with conn.cursor() as cur:
                                # А. Обновляем название локации
                                cur.execute(
                                    'UPDATE "DarkSouls".locations SET location_name = %s WHERE location_id = %s;',
                                    (new_name, loc_to_edit_id)
                                )

                                # Б. Перезаписываем связи с ВРАГАМИ
                                cur.execute('DELETE FROM "DarkSouls".enemies_locations WHERE location_id = %s;',
                                            (loc_to_edit_id,))
                                for en_name in updated_enemies:
                                    cur.execute(
                                        'INSERT INTO "DarkSouls".enemies_locations (enemy_id, location_id) VALUES (%s, %s);',
                                        (enemy_dict[en_name], loc_to_edit_id)
                                    )

                                # В. Перезаписываем связи с NPC
                                cur.execute('DELETE FROM "DarkSouls".npcs_locations WHERE location_id = %s;',
                                            (loc_to_edit_id,))
                                for n_name in updated_npcs:
                                    cur.execute(
                                        'INSERT INTO "DarkSouls".npcs_locations (npc_id, location_id) VALUES (%s, %s);',
                                        (npc_dict[n_name], loc_to_edit_id)
                                    )

                                # Г. Перезаписываем связи с ПРЕДМЕТАМИ
                                cur.execute('DELETE FROM "DarkSouls".items_locations WHERE location_id = %s;',
                                            (loc_to_edit_id,))
                                for it_name in updated_items:
                                    cur.execute(
                                        'INSERT INTO "DarkSouls".items_locations (item_id, location_id) VALUES (%s, %s);',
                                        (item_dict[it_name], loc_to_edit_id)
                                    )

                                conn.commit()
                            st.success(f"Локация '{new_name}' и её содержимое успешно обновлены!")
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Ошибка изменения структуры локации: {e}")

# --- ВКЛАДКА 7: УДАЛЕНИЕ ДАННЫХ ---
with tab7:
    st.header("Удаление сущностей из базы данных")
    st.write("Выберите объект для удаления. Система автоматически очистит связи, чтобы не нарушать целостность.")

    del_category = st.radio("Что будем удалять?", ["Локацию", "Врага / Босса", "Персонажа (NPC)", "Предмет"],
                            horizontal=True)
    st.markdown("---")

    if del_category == "Локацию":
        if location_dict:
            loc_to_del_name = st.selectbox("Выберите локацию для удаления:", list(location_dict.keys()),
                                           key="sb_del_loc")
            loc_to_del_id = location_dict[loc_to_del_name]

            if st.button(f"Удалить локацию '{loc_to_del_name}'", type="primary"):
                try:
                    with conn.cursor() as cur:
                        cur.execute('DELETE FROM "DarkSouls".enemies_locations WHERE location_id = %s;',
                                    (loc_to_del_id,))
                        cur.execute('DELETE FROM "DarkSouls".npcs_locations WHERE location_id = %s;', (loc_to_del_id,))
                        cur.execute('DELETE FROM "DarkSouls".items_locations WHERE location_id = %s;', (loc_to_del_id,))
                        cur.execute('DELETE FROM "DarkSouls".locations WHERE location_id = %s;', (loc_to_del_id,))
                        conn.commit()
                    st.success(f"Локация '{loc_to_del_name}' успешно удалена!")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"Ошибка удаления локации: {e}")
        else:
            st.info("Локаций в базе данных нет.")

    elif del_category == "Врага / Босса":
        if enemy_dict:
            enemy_to_del_name = st.selectbox("Выберите врага для удаления:", list(enemy_dict.keys()),
                                             key="sb_del_enemy")
            enemy_to_del_id = enemy_dict[enemy_to_del_name]

            if st.button(f"Удалить врага '{enemy_to_del_name}'", type="primary"):
                try:
                    with conn.cursor() as cur:
                        cur.execute('DELETE FROM "DarkSouls".enemies_locations WHERE enemy_id = %s;',
                                    (enemy_to_del_id,))
                        cur.execute('DELETE FROM "DarkSouls".enemies WHERE enemy_id = %s;', (enemy_to_del_id,))
                        conn.commit()
                    st.success(f"Враг '{enemy_to_del_name}' успешно удален из базы и локаций!")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"Ошибка удаления врага: {e}")
        else:
            st.info("Врагов в базе данных нет.")

    elif del_category == "Персонажа (NPC)":
        if npc_dict:
            npc_to_del_name = st.selectbox("Выберите персонажа для удаления:", list(npc_dict.keys()), key="sb_del_npc")
            npc_to_del_id = npc_dict[npc_to_del_name]

            if st.button(f"Удалить персонажа '{npc_to_del_name}'", type="primary"):
                try:
                    with conn.cursor() as cur:
                        cur.execute('DELETE FROM "DarkSouls".npcs_locations WHERE npc_id = %s;', (npc_to_del_id,))
                        cur.execute('DELETE FROM "DarkSouls".npc WHERE npc_id = %s;', (npc_to_del_id,))
                        conn.commit()
                    st.success(f"Персонаж '{npc_to_del_name}' успешно удален из базы и локаций!")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"Ошибка удаления персонажа: {e}")
        else:
            st.info("Персонажей в базе данных нет.")

    elif del_category == "Предмет":
        if item_dict:
            item_to_del_name = st.selectbox("Выберите предмет для удаления:", list(item_dict.keys()), key="sb_del_item")
            item_to_del_id = item_dict[item_to_del_name]

            st.warning(
                "⚠️ Удаление предмета автоматически обнулит ссылки на него (drop/награда) у всех связанных врагов и NPC!")
            if st.button(f"Удалить предмет '{item_to_del_name}'", type="primary"):
                try:
                    with conn.cursor() as cur:
                        cur.execute('UPDATE "DarkSouls".enemies SET item_id = NULL WHERE item_id = %s;',
                                    (item_to_del_id,))
                        cur.execute('UPDATE "DarkSouls".npc SET item_id = NULL WHERE item_id = %s;', (item_to_del_id,))
                        cur.execute('DELETE FROM "DarkSouls".items_locations WHERE item_id = %s;', (item_to_del_id,))
                        cur.execute('DELETE FROM "DarkSouls".items WHERE item_id = %s;', (item_to_del_id,))
                        conn.commit()
                    st.success(f"Предмет '{item_to_del_name}' успешно удален.")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"Ошибка удаления предмета: {e}")
        else:
            st.info("Предметов в базе данных нет.")