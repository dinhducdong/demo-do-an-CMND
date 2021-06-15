import os
class Config(object):
    DEBUG = False
    TESTING = False

    IMAGE_UPLOADS = "./app/static/idcard_images"
    IMAGE_UPLOADS2 = "./app/static/idface_images"
    IMAGE_UPLOADS3 = "./app/static/alignid_images"
    IMAGE_UPLOADS4 = "./app/static/orcid_images"
    CSRF_ENABLED = True
    SECRET_KEY = b"\xa6x\xf1$c\xddZ\xb8\xf8\x87u\x91\x7f\x0c\xcds'\x9e\xac\xb7\xb6\xc3\x9b\x10"

    AUTHY_API_KEY = 'YRcd6vIBKQzykL4XXg9dmPP9QaQCB16K'

    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:12345@localhost/ekyc_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BCRYPT_LOG_ROUNDS = 15
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_SSL = False
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'dongdinhnb@gmail.com'
    MAIL_PASSWORD = ''
    MAIL_DEFAULT_SENDER = '"Dong_Dinh" <dongdinhnb@gmail.com>'
    ADMINS = [
        '"Admin One" <dongdinhnb@gmail.com>',
    ]

class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    DEBUG = True

    IMAGE_UPLOADS = "./app/static/idcard_images"

class TestingConfig(Config):
    TESTING = True
