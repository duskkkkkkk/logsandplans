# 存放用于生成数据库模型的类
from extds import db
from datetime import datetime

# 用户表
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    name = db.Column(db.String(40), nullable=False, unique=True)
    password = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    icon = db.Column(db.String(200), nullable=False) # 用户的头像
    # 设置字段分别用于记录用户本次登录时间与上次的登录时间 用户注册时两者相一致
    login_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # 设置字段判断用户是否有设置当日计划
    set = db.Column(db.Boolean, nullable=False, default=False)
    # 用户表与建立外键的表的联系
    # 日志集合 括号内需要的参数是类名 以及通过log_set回溯到user所需的字段名
    log_sets = db.relationship('Logset', backref='user')
    today = db.relationship('Plan_today', backref='user')
    future = db.relationship('Plan_future', backref='user')
    daily = db.relationship('DailyPlan', backref='user')
    images = db.relationship('Userimage', backref='user')
    def __init__(self, name, password, phone, icon):
        self.name = name
        self.password = password
        self.phone = phone
        self.icon = icon

# 用户的日志集合表 每一条记录代表用户创建的一个日志集合
class Logset(db.Model):
    __table_name__ = 'logset'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    # 用户创建的日志集合名应当各不相同 若用户未指定集合名则系统会默认取名未untitledn
    name = db.Column(db.String(40), nullable=False, unique=True)
    # 日志集合的创建时间以及修改时间
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # 用户id的外键 创建外键关系时 定义联级删除参数 实现联级删除
    uid = db.Column(db.Integer,db.ForeignKey('user.id', ondelete='CASCADE'),nullable=False)
    # 外键对应关系
    logs = db.relationship('Log', backref='set')
    def __init__(self, name, uid):
        self.name = name
        self.uid = uid

# 日志表
class Log(db.Model):
    __table_name__ = 'log'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    title = db.Column(db.String(40), nullable=False, unique=True)
    # 存放文字资源所在的地址位置
    content = db.Column(db.String(200), nullable=False)
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # 是否优先显示
    focus = db.Column(db.Boolean, nullable=False, default=False)
    # Logset的外键
    set_id = db.Column(db.Integer, db.ForeignKey('logset.id', ondelete='CASCADE'),nullable=False)
    # 外键对应关系
    images = db.relationship('Logimages', backref='log')
    def __init__(self, title, content,set_id):
        self.title = title
        self.content = content
        self.set_id = set_id

# 日志的图片资源
class Logimages(db.Model):
    __table_name__ = 'logimages'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    # 图片资源所在的位置
    addr = db.Column(db.String(200),nullable=False)
    log_id = db.Column(db.Integer, db.ForeignKey('log.id', ondelete='CASCADE'),nullable=False)
    def __init__(self, addr, log_id):
        self.addr = addr
        self.log_id = log_id

# 当日计划
class Plan_today(db.Model):
    __table_name__ = 'plan_today'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # 检测当日计划是否完成
    finished = db.Column(db.Boolean, nullable=False, default=False)
    uid = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'),nullable=False)
    # 外键关系的联系
    details = db.relationship('Plan_today_detail', backref='plan_today')

    def __init__(self, uid):
        self.uid = uid

# 当日计划的具体条目
class Plan_today_detail(db.Model):
    __table_name__ = 'plan_today_detail'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    name = db.Column(db.String(40),nullable=False) # 条目名
    plan_type = db.Column(db.String(40)) # 计划种类 允许为空
    priority = db.Column(db.Integer, nullable=False, default=0) #优先级 默认为0
    finished = db.Column(db.Boolean, nullable=False, default=False) # 是否已经完成
    # 计划记录的外键
    pid = db.Column(db.Integer, db.ForeignKey('plan_today.id', ondelete='CASCADE'),nullable=False)

    def __init__(self, name, plan_type, priority, pid):
        self.name = name
        self.plan_type = plan_type
        self.priority = priority
        self.pid = pid


# 未来日程
class Plan_future(db.Model):
    __table_name__ = 'plan_future'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    name = db.Column(db.String(40),nullable=False)
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    remind_time = db.Column(db.Integer, nullable=False) # 提前提醒的时间 单位为天
    reminded = db.Column(db.Boolean, nullable=False, default=False) # 是否继续提醒 若用户设置不再提醒则设置为false
    # 外键关系
    uid = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'),nullable=False)
    # 外键联系
    details = db.relationship('Plan_future_detail', backref='plan_future')
    # 构造函数
    def __init__(self, name,end_time, inform_time, uid):
        self.name = name
        self.end_time =end_time
        self.remind_time =inform_time
        self.uid = uid

# 未来日程的具体条目
class Plan_future_detail(db.Model):
    __table_name__ = 'future_plan_detail'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    name = db.Column(db.String(40),nullable=False)
    plan_type = db.Column(db.String(40))
    tip = db.Column(db.String(100),nullable=False,default='无') # 条目的备注
    # 外键关系
    pid = db.Column(db.Integer, db.ForeignKey('plan_future.id', ondelete='CASCADE'),nullable=False)
    # 构造函数
    def __init__(self, name, plan_type, tip, pid):
        self.name = name
        self.plan_type = plan_type
        self.tip = tip
        self.pid = pid

# 日常计划
class DailyPlan(db.Model):
    __tablename__ = 'dailyplan' # tablename一定要正确设置
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    name = db.Column(db.String(40),nullable=False)
    reminded = db.Column(db.Boolean,nullable=False,default=False)
    # 外键关系
    uid = db.Column(db.Integer, db.ForeignKey('user.id',ondelete='CASCADE'),nullable=False)
    # 外键联系
    details = db.relationship('DailyPlan_detail', backref='dailyplan')
    # 构造函数
    def __init__(self, name, uid):
        self.name = name
        self.uid = uid

# 日常计划条目
class DailyPlan_detail(db.Model):
    __table_name__ = 'dailyplan_detail'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    name = db.Column(db.String(40),nullable=False)
    plan_type = db.Column(db.String(40))
    tip = db.Column(db.String(100),nullable=False,default='无') # 备注
    # 外键关系
    did = db.Column(db.Integer, db.ForeignKey('dailyplan.id', ondelete='CASCADE'),nullable=False)
    # 构造函数
    def __init__(self, name, plan_type, tip, did):
        self.name = name
        self.plan_type = plan_type
        self.tip = tip
        self.did = did

# 用户中心所展示的各种图像
class Userimage(db.Model):
    __table_name__ = 'userimage'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    addr = db.Column(db.String(200),nullable=False) # 用户相关图像的地址
    # 外键
    uid = db.Column(db.Integer, db.ForeignKey('user.id',ondelete='CASCADE'),nullable=False)
    def __init__(self, addr, uid):
        self.addr = addr
        self.uid = uid











