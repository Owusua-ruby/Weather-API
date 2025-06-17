from os import getcwd, path

from environs import Env

cwdir = getcwd()

env = Env()
env.read_env(path.join(cwdir, ".env"))

DEBUG = env.str("ENV") == "dev"
TAHMO_API_USERNAME = env.str("TAHMO_API_USERNAME")
TAHMO_API_PASSWORD = env.str("TAHMO_API_PASSWORD")
FORFECAST_API_KEY = env.str("FORFECAST_API_KEY")
