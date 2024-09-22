import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

#actions from firebase

#connect to firebase
cred = credentials.Certificate('private/weather-bot-46e02-firebase-adminsdk-u3xkq-3ce8852a30.json')  # Укажите путь к вашему serviceAccountKey.json
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://weather-bot-46e02-default-rtdb.firebaseio.com/'  # Укажите URL вашей Firebase Realtime Database
})


# creating a new user
def db_table_val(user_id: int, city: str = '', sex: int = -1, learning_data: str = ''):
    ref = db.reference('tpp_testbot')
    new_data = {
        'id': user_id,
        'user_id': user_id,
        'city': city,
        'sex': sex,
        'learning_data': learning_data
    }
    ref.push().set(new_data)


# updating user data
def update_data(user_id: int, city: str = None, sex: int = None, learning_data: str = None):
    ref = db.reference('tpp_testbot') 
    user_ref = ref.order_by_child('user_id').equal_to(user_id).get()
    if user_ref:
        user_key = list(user_ref.keys())[0]
        if city is not None:
            ref.child(user_key).update({'city': city})
        if sex is not None:
            ref.child(user_key).update({'sex': sex})
        if learning_data is not None:
            ref.child(user_key).update({'learning_data': learning_data})


# receiving user data
def get_data(user_id):
    ref = db.reference('tpp_testbot')
    user_ref = ref.order_by_child('user_id').equal_to(user_id).get()
    if user_ref:
        id = list(user_ref.values())[0]['id']
        user_id = list(user_ref.values())[0]['user_id']
        city = list(user_ref.values())[0]['city']
        sex = list(user_ref.values())[0]['sex']
        learning_data = list(user_ref.values())[0]['learning_data']
        data = id, user_id, city, sex, learning_data
        data = list(data)
        final = data, user_ref
        return final
    return []
