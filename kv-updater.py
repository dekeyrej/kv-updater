"""
step 2 in the Redis-first chain. This process listens to a Redis pub/sub channel,
extracts the key and payload from the received data, and persists it to the Redis KV store.

incoming data format:
{
    "type": "key",
    "updated": "2023-10-01T12:00:00Z",
    "valid": true,
    "values": {
        "field1": "value1",
        "field2": "value2"
    }
}

stored data format for Redis KV store:
key = {
        "updated": "2023-10-01T12:00:00Z",
        "valid": true,
        "values": {
            "field1": "value1",
            "field2": "value2"
        }
      }
"""
import json
from redis import Redis
import logging

logging.basicConfig(level=logging.INFO)

class KVUpdater:
    """
    Class to handle Redis KV store updates.
    """
    def __init__(self, redis_url: str, channel: str = 'update', validate: bool = False) -> None:
        self.client = Redis.from_url(redis_url, decode_responses=True)
        self.channel = channel
        self.validate = validate

    def persist_data(self, messagedata: str) -> None:
        """
        Persist data to Redis KV store.
        """
        try:
            data = json.loads(messagedata)
            key = data.get('type')
            payload = {
                "updated": data.get('updated'),
                "valid": data.get('valid'),
                "values": data.get('values')
            }

            if key and payload['values']:
                self.client.set(key, json.dumps(payload))
                logging.debug(f"Data persisted with key: {key}")
                if self.validate:
                    loaded_payload = self.client.get(key)  # This will raise an error if the key does not exist
                    if loaded_payload:
                        if json.loads(loaded_payload) == payload:
                            logging.info("Data validation successful.")
            else:
                logging.warning("Invalid message format. 'key' and 'payload' are required.")
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON message.")
        except Exception as e:
            logging.error(f"An error occurred while persisting data: {e}")

    def run(self) -> None:
        """
        Main function to listen to Redis pub/sub channel and persist data.
        """
        pubsub = self.client.pubsub()
        pubsub.subscribe(self.channel)

        logging.info(f"Listening for messages on '{self.channel}'...")

        try:
            while True:
                for message in pubsub.listen():
                    if message['type'] == 'message':
                        self.persist_data(message['data'])
        except KeyboardInterrupt:
            logging.info("Stopped listening for messages.")
        finally:
            pubsub.unsubscribe()
            pubsub.close()
            self.client.close()


if __name__ == "__main__":

    from config import config

    redis_url = config.get('redis_url', 'redis://redis.redis:6379/0')
    channel = config.get('channel', 'update')
    validate = config.get('validate', False)

    KVUpdater(redis_url, channel, validate).run()