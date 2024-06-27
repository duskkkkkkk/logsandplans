# 存放各种蓝图的模块
from flask import Flask
from apps.user.view import view
import settings
import model
from extds import db
# 导入蓝图对象 注意导入时应使用.连接包中的各个文件路径 直到指向蓝图文件所在的文件中
# 配置app对象的函数 这个就是一个工厂函数
def create_app():
    app=Flask(__name__,template_folder='../templates',static_folder='../static')# 创建对象 注意要配置好参数中的路径 ../表示上一级的目录
    app.config.from_object(settings.DevelopmentConfig)# 加载开发配置
    # 在app对象上注册蓝图 括号内的参数为蓝图名
    app.register_blueprint(view)
    # 关联数据库操纵对象以及app对象
    db.init_app(app)  # 将db对象与app进行关联
    return app #app的程序中的核心对象 所有的第三方的部分都需要于app相连接
