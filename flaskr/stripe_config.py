import os

# INTEGRATION NOTE #5: cupdate stripe configeration
def set_environ():
    os.environ['STRIPE_SECRET_KEY'] = 'sk_test_51IJKWhBqrfVtgI4XstKyjdhhiUILSh6fLvQk2happe2XGhJqWF3wnxe9E2E7xQZ6HUFbrYcrhqzRZz7r8DWKU0zi00U8vZXHVU'
    os.environ['currency'] = 'usd'
    os.environ['logo'] = 'http://bot.talentinobot.com/static/img/MainLogo.png'
