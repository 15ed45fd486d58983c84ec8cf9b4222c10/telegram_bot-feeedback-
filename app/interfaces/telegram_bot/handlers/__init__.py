from .complain import register_complain_handler


def register_handlers(dp):
    register_complain_handler(dp)
