import sqlite3

# operations with the local database

# create a user in the database
def db_table_val(user_id: int, city: str, sex: int, learning_data: str):
    conn = sqlite3.connect('database/bot_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tpp_testbot (user_id, city, sex, learning_data) VALUES (?, ?, ?, ?)',
                   (user_id, city, sex, learning_data))
    conn.commit()
    conn.close()


# update user data
def update_data(user_id: int, city: str = None, sex: int = None, learning_data: str = None):
    conn = sqlite3.connect('database/bot_data.db')
    cursor = conn.cursor()
    if city is not None:
        cursor.execute('UPDATE tpp_testbot SET city=? WHERE user_id=?', (city, user_id))
    if sex is not None:
        cursor.execute('UPDATE tpp_testbot SET sex=? WHERE user_id=?', (sex, user_id))
    if learning_data is not None:
        cursor.execute('UPDATE tpp_testbot SET learning_data=? WHERE user_id=?', (learning_data, user_id))
    conn.commit()
    conn.close()


# get user data
def get_data(user_id):
    conn = sqlite3.connect('database/bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tpp_testbot WHERE user_id = ?', (user_id,))
    data = cursor.fetchall()
    conn.close()
    return data
