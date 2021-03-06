import asyncio
import json
import logging
from os import environ

import websockets
import pymongo
import dotenv
from bson import ObjectId

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(message)s", datefmt="%d-%b-%y %H:%M:%S"
)
dotenv.load_dotenv()

USERS = set()

# SetUp the database for mongo
client = pymongo.MongoClient(environ.get("MONGO_URL"))
db = client.robin_hood
logging.info("Database conection successfully's")


def get_notifications():
    """
    Returns all notifications from specific user

    Params:
        user_id (str): User id.
    """
    filter = {"is_active": True}
    notifications = db.notifications.find(filter)
    return list(notifications)


async def set_inactive_notification(notification: dict):
    filters = {"_id": ObjectId(notification["_id"])}
    notification["_id"] = ObjectId(notification["_id"])
    notification["is_active"] = False
    db.notifications.replace_one(filters, notification)
    logging.info(f"Se cambio el active a false _id:{str(notification['_id'])}")


def send_notifications_event():
    notifications = get_notifications()
    for notification in notifications:
        notification["_id"] = str(notification["_id"])

    return json.dumps({"type": "notification", "data": notifications})


def user_event():
    logging.info(f"Total of users: {len(USERS)}")


async def notification_event():
    if USERS:
        message = send_notifications_event()
        await asyncio.wait([user.send(message) for user in USERS])


def register(websocket):
    USERS.add(websocket)
    user_event()


def unregister(websocket):
    USERS.remove(websocket)


async def notify_event():
    return await notification_event()


async def server(websocket, path):
    register(websocket)
    try:
        await notification_event()
        async for message in websocket:
            data = json.loads(message)
            if data["action"] == "notify":
                await notify_event()
            if data["action"] == "seen":
                await set_inactive_notification(data["notification"])
            else:
                logging.error(f"unsopported event: {data}")
    finally:
        unregister(websocket)


start_server = websockets.serve(server, "0.0.0.0", 6789)
logging.info("Server started")

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
