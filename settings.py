import os


class Config(object):
    DEBUG = True
    # 连接mysql数据库的相关设置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@127.0.0.1:3306/finaltest'
    SQLALCHEMY_ECHO =True
    SQLALCHEMY_TRACK_MODIFICATIONS =False
    SECRET_KEY = 'pythonfinaltest'
    # 项目资源的存储路径
    BASE_DIR=os.path.dirname(os.path.abspath(__file__)) # path后面表示获取到当前路径文件的文件夹
    # 静态资源的存储位置
    STATIC_DIR=os.path.join(BASE_DIR,'static') # join表示拼接 就是再当前文件之后再拼接上static
    # 模板资源的存储位置
    TEMPLATE_DIR=os.path.join(BASE_DIR,'templates')
    # 图片资源的存储位置 仅到达最外层的文件夹
    IMG_DIR=os.path.join(STATIC_DIR,'images')
    USER_DIR=os.path.join(BASE_DIR,'users')

# 开发模式
class DevelopmentConfig(Config):
    ENV='development'
# 结算模式
class FinishedConfig(Config):
    ENV='finished'