import extra_streamlit_components as stx
import time


def get_manager():
    manager = stx.CookieManager(key="init_cookie_manager")
    time.sleep(0.1)
    return manager
