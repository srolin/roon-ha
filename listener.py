import paho.mqtt.client as mqtt
import time
import requests

roon_zones = {'Family Room': {'action': 'harmony post',
                              'action_value': 'http://192.168.1.38:8282/hubs/family-room/activities/listen-to-music',
                              'turn_off_after_paused_for': 350
                              },
              'Living Room': {'action': None
                              }
              }
paused_zone_states = dict()


def get_connected_client(client_id :str, broker_address :str ):
    client = mqtt.Client(client_id)
    client.connect(broker_address)
    return client


def subscribe_to_roon_zone(mqtt_client, zones):
    for zone in zones:
        res = mqtt_client.subscribe(f'roon/{ zone }/state')
        if res[0] == 0:
            print(f'successfully subscribed to topic: roon/{ zone}/state')
        else:
            print(f'Unable to subscribe to topic: roon/{ zone }/state')


def process_roon_zone_states(client, userdate, message):
    for zone in roon_zones:
        if message.topic == f'roon/{ zone }/state':
            state = str(message.payload.decode('utf-8'))
            if state == 'paused':
                paused_zone_states[zone] = time.time()
            elif state == "playing":
                if zone in paused_zone_states:
                    del paused_zone_states[zone]
                if roon_zones[zone]['action'] == 'harmony post':
                    res = requests.post(roon_zones[zone]['action_value'])
            print(paused_zone_states)


def process_messages(client, userdata, message):
    print(message.topic)
    if message.topic[0:5] == "roon/" and message.topic[-6:] == '/state':
        process_roon_zone_states(client, userdata, message)

def stop_zone(zone_name):
    res = requests.get('http://192.168.1.38:8282/hubs/family-room/status')
    if res.status_code == 200:
        body = res.json()
        if body['current_activity']['slug'] == 'listen-to-music':
            res = requests.put('http://192.168.1.38:8282/hubs/family-room/off')

    pass


def check_zone_timeouts():
    for zone_name in paused_zone_states:
        now = time.time()
        paused_for = int(now - paused_zone_states[zone_name])
        if 'turn_off_after_paused_for' in roon_zones[zone_name]:
            if paused_for > roon_zones[zone_name]['turn_off_after_paused_for']:
                stop_zone(zone_name)


mq_client = get_connected_client("L1", "192.168.1.38")
subscribe_to_roon_zone(mq_client, roon_zones)
mq_client.on_message = process_messages

print('Starting the loop')
mq_client.loop_start()
while True:
    time.sleep(1)
    check_zone_timeouts()

