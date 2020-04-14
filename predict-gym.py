import os
import gym
import sys
import pandas as pd
import numpy as np
from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common.policies import CnnPolicy
from stable_baselines.common.policies import CnnLstmPolicy
from stable_baselines.common.vec_env import DummyVecEnv
from stable_baselines import PPO2
from stable_baselines import DQN
from stable_baselines import A2C
from env.trading_coin_env import TradingCoinEnv

props = {
    #начальный баланс на счете
    'balance_init': 4000,

    #начальное кол-во монет на счете
    'coins_init': 200,

    #на сколько частей можно разбить доступный остасток для покупки/продажи, 
    #т.е. покупать не на всю доступную сумму а на ее часть
    'balance_parts': 5,

    #сколько минут истории надо учитывать для обучения
    'history_analise_minutes': 900,

    #максимальное время удержания позиции (в минутах)
    'max_minutes_hold_pos': 800,

    #сколько секунд в одном интервале
    'seconds_in_intrerval': 15,

    #сколько исторических интервалов до текущего надо учитывать
    #'lookback_window_size': 20

    #максимальная просадка в %
    'max_loss': 20
}

class Config:
    def __init__(self, **entries):
        self.__dict__.update(entries)

#props to object
cfg = Config(**props)

#read data from file
DATASET_PATH = "data"

def prepare_df(fileName):
    file_name = os.path.join(os.path.dirname(__file__), DATASET_PATH + "/" + fileName)
    df = pd.read_csv(file_name)
    df.rename(columns=lambda x: x.strip(), inplace=True)
    df['avrPrice'] = df['avrPrice'].replace(to_replace=0, method='ffill')

    return df

df = prepare_df("binanceOpenAi-20191126-20191231.dat")

env = TradingCoinEnv(df, cfg)
#env = DummyVecEnv([lambda: env])

analize_row_cnt = int(cfg.history_analise_minutes * 60 / cfg.seconds_in_intrerval)
result_all = pd.DataFrame()

for ind in range(7, 10):
    fileModel = os.path.dirname(__file__) + "/trained_models/ppo/model_" + str(ind)
    print(fileModel)

    model = PPO2.load(fileModel)

    obs = env.reset()
    env.set_first_index()

    for i in range(df.shape[0] - analize_row_cnt - 20):
        action, _states = model.predict(obs)

        if (i % 500 == 0):
            print(i)

        obs, rewards, done, info = env.step(action)
        if (done == True):
            print ('Done = true')

    row_result = env.render()
    result_all = result_all.append(row_result, ignore_index=True)

result_all.columns = ['order_count', 'usd_change', 'coins_change', 'profit']

print (f'result = {result_all}')
result_all.to_csv(r'./result_all.txt', sep='\t')
