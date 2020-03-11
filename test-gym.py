import os
import gym
import pandas as pd
from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common.vec_env import DummyVecEnv
from stable_baselines import PPO2

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
    'max_minutes_hold_pos': 600,

    #сколько секунд в одном интервале
    'seconds_in_intrerval': 15,

    #сколько исторических интервалов до текущего надо учитывать
    #'lookback_window_size': 20
}

class Config:
    def __init__(self, **entries):
        self.__dict__.update(entries)

#props to object
cfg = Config(**props)

#read data from file
DATASET_PATH = "data"
file_name = os.path.join(os.path.dirname(__file__), DATASET_PATH + "/binanceOpenAi-jan.dat")
df = pd.read_csv(file_name)
df.rename(columns=lambda x: x.strip(), inplace=True)

# The algorithms require a vectorized environment to run
#env = DummyVecEnv([lambda: TradingCoinEnv(df, cfg)])

te = TradingCoinEnv(df, cfg)