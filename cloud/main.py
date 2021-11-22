#!/usr/bin/env python3
import os
from config import load_config
from parts.datastore import TubGroup
from parts.keras import KerasLinear
import tensorflow as tf
from flask import Flask, request
from flask import jsonify
from celery import Celery
import json
import re
import redis

app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = os.environ['BROKER_URL']
app.config['CELERY_RESULT_BACKEND'] = os.environ['RESULT_BACKEND_URL']

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


def get_redis_connect(address):
    reg = r'redis://(.*?):(\d+)'
    m = re.search(reg, address)
    r = redis.StrictRedis(host=m.group(1), port=m.group(2))
    return r


@celery.task(bind=True)
def train_model(self, tub_path, model_path, epochs, batch_size, train_test_split, ):
    gpu_devices = tf.config.experimental.list_physical_devices('GPU')
    for device in gpu_devices:
        tf.config.experimental.set_memory_growth(device, True)
    '''
    use the specified data in tub_names to train an artifical neural network
    saves the output trained model as model_name
    '''
    X_keys = ['cam/image_array']
    Y_keys = ['user/angle', 'user/throttle']

    kl = KerasLinear()

    tub_path = os.path.expanduser(tub_path)
    tubgroup = TubGroup(tub_path)
    train_gen, val_gen = tubgroup.get_train_val_gen(X_keys, Y_keys, batch_size=batch_size,
                                                    train_frac=train_test_split)

    model_path = os.path.expanduser(model_path)
    total_records = len(tubgroup.df)
    total_train = int(total_records * train_test_split)
    steps_per_epoch = total_train // batch_size

    task_id = train_model.request.id
    r = get_redis_connect(os.environ['BROKER_URL'])
    r.hset(task_id, key="epoch", value=0)
    r.hset(task_id, key="loss", value=1)
    self.update_state(state='PROGRESS')
    kl.train(train_gen, val_gen, saved_model_path=model_path, steps=steps_per_epoch, train_split=train_test_split,
             epochs=epochs, redis_connect=r, task_id=task_id)
    self.update_state(state='SUCCESS')
    r.close()


@app.route('/train', methods=['POST'])
def train():
    cfg = load_config()
    data_path = request.form['data_path']
    models_path = os.path.join(data_path, 'model')
    task = train_model.delay(data_path, models_path, cfg.EPOCHS, cfg.BATCH_SIZE, cfg.TRAIN_TEST_SPLIT)
    return jsonify({'task_id': task.id})


@app.route('/status', methods=['POST'])
def task_status():
    task_id = request.form['task_id']
    task = train_model.AsyncResult(task_id)
    r = get_redis_connect(os.environ['BROKER_URL'])
    epoch = int(r.hget(task_id, "epoch"))
    loss = float(r.hget(task_id, "loss"))
    r.close()
    response = jsonify({
        "state": task.state,
        "epoch": epoch,
        "loss": loss
    })
    return response


if __name__ == '__main__':
    app.run("0.0.0.0", 8080)
