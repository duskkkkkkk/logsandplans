# 存放用户相关方法的视图函数的py文件
from flask import Blueprint,request,url_for,render_template,redirect,flash,session,jsonify
from werkzeug.utils import secure_filename

# 引入模型中的类
from model import User,Logset,Log,Logimages,Plan_today,Plan_today_detail,Plan_future,Plan_future_detail,DailyPlan,DailyPlan_detail
from extds import db
from settings import DevelopmentConfig
import hashlib
import os
import time
from datetime import datetime, date, timedelta

# 生成蓝图对象
view = Blueprint("view_u",__name__)

# 通用函数区
# 通过plan_id 来查询到所有的details
def searchtoday_by_id(plan_id):
    details = Plan_today_detail.query.filter_by(pid = plan_id).all()
    return details

def searchfuture_by_id(plan_id):
    # 通过id来获取到相应的细节并将其封装成dict返回
    details = Plan_future_detail.query.filter_by(pid = plan_id).all()
    base_info = Plan_future.query.filter_by(id = plan_id).first()
    # 初始化base_info
    today = date.today()
    # 获取到当日距ddl的时间 注:两个datetime之间相减获取到的是一个datetime的对象 通过date对象的days即可获取到相应的天数
    ddl_days = (base_info.end_time.date() - today).days
    # 获取到当日距离remind的时间
    remind_days = ddl_days - base_info.remind_time
    remind = today + timedelta(days=remind_days)
    # 构建对象
    info_trans = {'name':base_info.name,'ddl':str(base_info.end_time.date()),'ddl_days':ddl_days,'remind':str(remind),'remind_days':remind_days,'reminded':base_info.reminded}
    # 封装具体细节的列表
    details_trans = []
    for detail in details:
        details_trans.append({'name':detail.name,'type':detail.plan_type,'tip':detail.tip})

    return {'details':details_trans, 'base_info':info_trans}

def searchsets(uid):
    # 通过用户的uid查询用户所有的日志集 并将其封装为列表返回
    sets = Logset.query.filter_by(uid = uid).all()
    # 创建传输的对象 包括创建时间 更新时间 名字 id 还有所包含的日志数目
    details = []
    for logset in sets:
        details.append(
            {'id':logset.id,'name': logset.name, 'create': str(logset.create_time.date()), 'update': str(logset.update_time.date()),
             'num': len(logset.logs)})

    return details

def searchlogs(id):
    # 通过日志集的id 来查询到其内所有的日志
    logset = Logset.query.filter_by(id = id).first()
    logs = logset.logs
    details_focus = []
    details_unfocus = []
    for log in logs:
        # 首先获取到当前log所有的图片资源
        pic = []
        for image in log.images:
            pic.append(image.addr)
        # 数据库内为文件地址 再通过地址获取到文字资源
        f = open(DevelopmentConfig.USER_DIR+'/'+str(session['uid'])+'/'+'text/'+log.content,'r')
        content = f.read()
        f.close()
        if log.focus:
            details_focus.append({'id':log.id,'name':log.title, 'content':content, 'create':str(log.create_time.date()), 'focus':log.focus,'pic':pic})
        else:
            details_unfocus.append({'id':log.id,'name':log.title, 'content':content, 'create':str(log.create_time.date()), 'focus':log.focus,'pic':pic})
    # 更新创建的排在前面
    details_focus.reverse()
    details_unfocus.reverse()
    details = details_focus+details_unfocus
    return details

# 用户每次登录时都会更新用户的状态
def update(uid):
    # 更新用户的登录状态
    user = User.query.filter_by(id = uid).first()
    last_time = user.login_time.date()
    user.login_time = datetime.now()
    # 根据用户登录事件的间隔来修改用户的当日计划的set
    if (user.login_time.date() - last_time).days >= 1:
        user.set = 0
    else:
        pass
    db.session.commit()
    # 自动取消提醒用户未手动设置不提醒且一过ddl的未来计划
    useless = Plan_future.query.filter_by(uid = uid and Plan_future.end_time <= datetime.now()).all()
    for plan in useless:
        plan.reminded = True
        db.session.commit()

    return

# 拦截函数的设定 未经登录 无法进入系统
@view.before_app_request
def before():
    need_confirm = ['/firstpage', '/today', '/showtoday','/finish','/setfuture','/showfuture','/setdaily','showdaily','/showset','/showcontent']
    if request.path in need_confirm:
       id=session.get('uid')
       if not id:
           return redirect(url_for('view_u.login'))
       else:
           pass

@view.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm=request.form['confirm']
        phone = request.form['phone']
        # 设置默认头像
        icon = os.path.join(DevelopmentConfig.STATIC_DIR,'pic1.png')
        if password != confirm:
            # 确认密码与密码不一致 返回错误消息
            msg = '确认密码与密码不一致 请重新输入'
            return msg
        else:
            password = hashlib.md5(password.encode()).hexdigest() # 使用md5方法对密码进行加密
            user = User(username,password,phone,icon)
            db.session.add(user)
            db.session.commit()
            # 搜寻出最新注册的用户 用其信息创建相关资源
            users = User.query.filter(User.name == username).all()
            user = users[len(users)-1]
            session['uid']=user.id
            # flag=1
            # 注册的同时在user内部创建一个文件夹 名字与用户id即主键相一致
            index_dir = os.path.join(DevelopmentConfig.USER_DIR,str(user.id))
            os.mkdir(index_dir)
            # 在用户名命名的文件夹内创建存放图片以及日志内容的目录
            os.mkdir(os.path.join(index_dir,'text')) # 存放文字内容
            # 创建存放图片内容的文件夹
            img_dir = os.path.join(DevelopmentConfig.STATIC_DIR,'uploads')
            os.mkdir(os.path.join(img_dir,str(user.id)))
            return redirect(url_for('view_u.firstpage'))
    else:
        return render_template('base_template/register.html')


# 用户的登录操作
@view.route("/",methods=["GET","POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password = hashlib.md5(password.encode()).hexdigest()
        users = User.query.filter(username==username).all()
        for user in users:
            if user.password == password:
                # 登录成功之后需要更新用户的登录数据
                session['uid'] = user.id
                update(session['uid'])
                return redirect(url_for('view_u.firstpage'))
        else:
            # 为找到匹配用户 返回错误信息
            errmsg='用户名或者密码错误'
            # 这里还是部分返回
            return errmsg
    else:
        return render_template('base_template/login.html')

# 用户登录之后进入首页
@view.route("/firstpage",methods=["GET","POST"])
def firstpage():
    if request.method == 'POST':
        # 当前端以post方式传递消息时 传递相关信息
        # 获取用户基本信息
        user = User.query.filter_by(id = session['uid']).first()
        user_info = {
            'name':user.name,
            'time':str(datetime.now().date())
        }
        # 获取用户相关计划信息
        # 当日计划
        if not user.set:
            # 用户尚未设置计划
            today_info = {'flag':0,'finished':0,'unfinished':0}
        else:
            details = Plan_today.query.filter_by(uid = session['uid']).all()
            details = details[len(details)-1].details
            finished = 0
            unfinished = 0
            for detail in details:
                if detail.finished:
                    finished += 1
                else:
                    unfinished += 1
            today_info = {'flag':1,'finished':finished,'unfinished':unfinished}
        # 未来日程
        # 首先获取到当前用户所有reminded为false的未来日程
        future_plans = Plan_future.query.filter_by(uid = session['uid'] and Plan_future.reminded == False).all()
        # 获取到所有提醒事件距离今天的日期 并计算再提醒日期内的计划数目
        future_count = 0
        for plan in future_plans:
            today = date.today()
            remind = (plan.end_time.date() - today).days - plan.remind_time
            if remind < 0:
                future_count += 1
        # 日常计划
        daily_plans = DailyPlan.query.filter_by(uid = session['uid'] and DailyPlan.reminded == False).all()
        daily_count = len(daily_plans)
        return jsonify({'user':user_info,'finished':{'today':today_info,'future':future_count,'daily':daily_count}}),200
    else:
        return render_template('base_template/firstpage.html')

@view.route("/logout",methods=["GET","POST"])
def logout():
    session.clear()
    return redirect(url_for('view_u.login'))

# 当日计划的设定
@view.route('/today',methods=["GET","POST"])
def set_today():
    if request.method == 'POST':
        # 使用user.id创建一个当日计划的对象
        today_plan = Plan_today(session['uid'])
        db.session.add(today_plan)
        db.session.commit()
        get_plans = Plan_today.query.filter_by(uid=session['uid']).all()
        get_today_plan = get_plans[len(get_plans)-1] # 获取到当前用户最新的计划记录
        # 创建当前用户计划具体条目
        # 通过axios传递的数据通过request.json来接收用户创建的日程数据
        results = request.json['results']
        print(results)
        for result in results:
            detail = Plan_today_detail(result['name'],result['type'],result['priority'],get_today_plan.id)
            db.session.add(detail)
            db.session.commit()
        # 同时将当日计划的标志变量设置为true
        get_user = User.query.filter_by(id=session['uid']).first()
        get_user.set = True
        db.session.commit()
        session['today_set'] = get_user.set

        return jsonify({'message':'success'}),200
    else:
        return render_template('base_template/settoday.html')

# 当日计划的展示以及完成情况的修改
@view.route('/finish',methods=["GET","POST"])
def get_details():
    if request.method == 'POST':
        # 当为post传值时向前端传递计划细节
        # 首先获取到最新一条的当日计划的id 注：此函数以及相关页面只有再设定计划之后才可见
        plans = Plan_today.query.filter_by(uid = session['uid']).all()
        plan_today = plans[len(plans)-1]
        # 通过当日设定计划的id来获取到设定计划的细节
        details = Plan_today_detail.query.filter_by(pid = plan_today.id).all()
        # 构造传递到前端的字符串
        trans_details = []
        for detail in details:
            trans_details.append({'id':detail.id,'name':detail.name,'type':detail.plan_type,'priority':detail.priority,'finished':detail.finished})
        # 添加结束之后将对列表进行排序 按照优先级的先后顺序排 小的在前 大的在后
        trans_details.sort(key=lambda x:x['priority'])

        return jsonify({'details':trans_details}),200
    else:
        return render_template('base_template/finish.html')

# 当日日志完成情况的改变
@view.route('/changefinish',methods=["GET","POST"])
def change_finish():
    # 当传输方式为post时改变finish的值
    if request.method == 'POST':
        # 通过前端获取到detail的id
        detail_id = request.json['detail_id']
        finished = bool(request.json['finished'])
        # 通过detail_id 获取到detail对象 一定要加上first 要不然就无法得到对象 得到的是查询语句
        detail = Plan_today_detail.query.filter_by(id = detail_id).first()
        detail.finished = finished
        db.session.commit()
        # 再次查询数据库 获取到所有同一天的完成情况并返回
        # 就需要通过那个relationship来通过detail定位到相应的plan对象了
        plan_today = detail.plan_today
        finished = 0
        unfinished = 0
        for detail in plan_today.details:
            if detail.finished:
                finished += 1
            else:
                unfinished += 1
        return jsonify({'msg':'success','finished':finished,'unfinished':unfinished}),200
    else:
        pass

# 展示今天以及曾经指定过的当日计划 只需完成首次的展示即可
@view.route('/showtoday',methods=["GET","POST"])
def show_today():
    # 首先获取到用户所有的plan_today的id信息
    if request.method == 'POST':
        plans_data = Plan_today.query.filter_by(uid = session['uid']).all()
        plans = []
        for plan in plans_data:
            # 通过plan.id首先查到所有的细节以获取完成情况
            details = searchtoday_by_id(plan.id)
            finished = 0
            unfinished = 0
            for detail in details:
                if detail.finished:
                    finished +=1
                else:
                    unfinished +=1
            plans.append({'id':plan.id,'date':str(plan.create_time.date()),'finished':finished,'unfinished':unfinished})
        # 同时查询最新的一次记录的相关细节
        plans.reverse()
        details_data = searchtoday_by_id(plans[0]['id'])
        details = []
        for detail in details_data:
            details.append({'id':detail.id,'name':detail.name,'type':detail.plan_type,'priority':detail.priority,'finished':detail.finished})
        return jsonify({'details':details,'plans':plans}),200 # 传过去的数据没问题
    else:
        return render_template('base_template/show_today.html')

# 通过路由来调用通过id查细节的函数 同时将查询结果封装成字典
@view.route('/searchtoday',methods=["GET","POST"])
def searchtoday_details():
    if request.method == 'POST':
        plan_id = request.json['id']
        details_data = searchtoday_by_id(plan_id)
        details = []
        for detail in details_data:
            details.append({'id': detail.id, 'name': detail.name, 'type': detail.plan_type, 'priority': detail.priority,'finished': detail.finished})

        return jsonify({'details':details})
    else:
        pass

# 设置未来日程的细节
@view.route('/setfuture',methods=["GET","POST"])
def setfuture():
    if request.method == 'POST':
        # 首先获取到未来日程的基本信息并将来创建一个未来日程的元组
        pname = request.json['base_info']['name']
        ddl = request.json['base_info']['ddl']
        remind_time = request.json['base_info']['remind']
        plan_new = Plan_future(pname,ddl,remind_time,session['uid'])
        db.session.add(plan_new)
        db.session.commit()
        # 查询此用户未来日程的最新元组获取其id
        fplans = Plan_future.query.filter_by(uid = session['uid']).all()
        fplan = fplans[len(fplans)-1]
        fid = fplan.id
        # 根据传输过来的细节创建日程条目
        details = request.json['results']
        for detail in details:
            f_detail = Plan_future_detail(detail['name'],detail['type'],detail['tip'],fid)
            db.session.add(f_detail)
            db.session.commit()

        return jsonify({'msg':'success'})
    else:
        return render_template('base_template/setfuture.html')

# showfuture 展示未来日程的页面
@view.route('/showfuture', methods=['GET','POST'])
def showfuture():
    if request.method == 'POST':
        # 执行初始化相关操作 从数据库中查询details 以及 future_plans
        # 查询plans
        fplans = Plan_future.query.filter_by(uid=session['uid']).all()
        trans_plans = []
        for plan in fplans:
            today = date.today()
            remind = (plan.end_time.date() - today).days - plan.remind_time
            # 需要向前端reminded信息 以初始化复选框
            trans_plans.append({'id':plan.id,'name':plan.name,'create_time':str(plan.create_time.date()),'end_time':str(plan.end_time.date()),'remind':remind,'reminded':plan.reminded})
        # 通过提醒时间的先后对列表中的元素进行排序
        trans_plans.sort(key=lambda x:x['remind'])
        plan_id = fplans[len(fplans)-1].id
        trans_info = searchfuture_by_id(plan_id)

        return jsonify({'details':trans_info,'plans':trans_plans})
    else:
        return render_template('base_template/showfuture.html')

# 查询未来条目的相关信息 并传入前端界面
@view.route('/searchfuture', methods=['GET','POST'])
def searchfuture():
    if request.method == 'POST':
        plan_id = request.json['id']
        trans_info = searchfuture_by_id(plan_id)

        return jsonify(trans_info),200

# 当checkbox传来消息时 修改数据库中的提醒状态
@view.route('/remindfuture', methods=['GET','POST'])
def change_remind():
    if request.method == 'POST':
        plan_id = request.json['plan_id']
        # 搜索到相应的future_plan
        plan = Plan_future.query.filter_by(id=plan_id).first()
        # 切换提醒状态 对当前数据库内的提醒状态取反
        print(plan.reminded)
        if plan.reminded:
            plan.reminded = False
        else:
            plan.reminded = True
        flag = plan.reminded
        db.session.commit()
        # 将reminded修改后的值返回前端 以修改下方的状态
        return jsonify({'flag':flag}),200


# 设置日常计划的页面
@view.route('/setdaily', methods=['GET','POST'])
def setdaily():
    # 获取前台的数据再将其插入数据库即可
    if request.method == 'POST':
        results = request.json['results']
        name = request.json['name']
        # 创建日常计划的对象
        dplan = DailyPlan(name,session['uid'])
        db.session.add(dplan)
        db.session.commit()
        # 查询当前用户最新的dailyplan对象
        plans = DailyPlan.query.filter_by(uid = session['uid']).all()
        plan = plans[len(plans)-1]
        plan_id = plan.id
        # 利用前端获取的具体条目以及pid创建条目对象
        for result in results:
            plan_detail = DailyPlan_detail(result['name'],result['type'],result['tip'],plan_id)
            db.session.add(plan_detail)
            db.session.commit()

        return jsonify({'msg':'成功创建对象'}),200
    else:
        return render_template('base_template/setdaily.html')


# 展示用户设定的所有的日常计划
@view.route('/showdaily', methods=['GET','POST'])
def showdaily():
    # 当前台传递信息时 需要返回details 和 plans 其中details与future类似 是一个对象/字典 而plans是一个列表
    if request.method == 'POST':
        # 首先查询到此用户所订立的所有的日常计划
        dplans = DailyPlan.query.filter_by(uid = session['uid']).all()
        trans_plans = []
        for dplan in dplans:
            trans_plans.append({'id':dplan.id,'name':dplan.name,'reminded':dplan.reminded})
        trans_plans.reverse()
        # 初始显示当前用户的最新订立的计划细节
        show_plan = dplans[len(dplans)-1]
        # 注意可以通过对象的方式获取到plan所有的细节 而不用查询
        plan_details = show_plan.details
        trans_details = []
        for detail in plan_details:
            trans_details.append({'name':detail.name,'type':detail.plan_type,'tip':detail.tip})
        base_info = {'name':show_plan.name,'reminded':show_plan.reminded}
        trans_details = {'base_info':base_info,'details':trans_details}

        return jsonify({'details':trans_details,'plans':trans_plans})
    else:
        return render_template('base_template/showdaily.html')

# 查询某一个日常计划的信息并返回给前端用于更新盒子内容 前端需要name和details
@view.route('/searchdaily', methods=['GET','POST'])
def searchdaily():
    if request.method == 'POST':
        # 获取dailyplan的id
        plan_id = request.json['id']
        plan = DailyPlan.query.filter_by(id = plan_id).first()
        # 获取到plan的各个detail
        details = plan.details
        trans_details = []
        for detail in details:
            trans_details.append({'name':detail.name,'type':detail.plan_type,'tip':detail.tip})
        base_info = {'name':plan.name,'reminded':plan.reminded}
        return jsonify({'details':trans_details,'base_info':base_info})
    else:
        pass

@view.route('/changedaily', methods=['GET','POST'])
def changedaily():
    if request.method == 'POST':
        plan_id = request.json['plan_id']
        # 搜索到相应的future_plan
        plan = DailyPlan.query.filter_by(id=plan_id).first()
        # 切换提醒状态 对当前数据库内的提醒状态取反
        if plan.reminded:
            plan.reminded = False
        else:
            plan.reminded = True
        flag = plan.reminded
        db.session.commit()
        # 将reminded修改后的值返回前端 以修改下方的状态
        return jsonify({'flag':flag}),200

# 创建日志相关
# 展示日志集合 查询数据库内的数据并将其传递到前端
@view.route('/showset', methods=['GET','POST'])
def showset():
    if request.method == 'POST':
        return jsonify({'details':searchsets(session['uid'])}),200
    else:
        return render_template('base_template/logset.html')

# 创建日志集合 在用户注册时会默认有一个日志集合
@view.route('/createset', methods=['GET','POST'])
def createset():
    if request.method == 'POST':
        plan_name = request.json['name']
        # 创建日志集对象
        newset = Logset(plan_name,session['uid'])
        db.session.add(newset)
        db.session.commit()
        # 创建传输的对象 包括创建时间 更新时间 名字 id 还有所包含的日志数目
        details = searchsets(session['uid'])
        return jsonify({'details':details}),200
    else:
        pass

# 删除一个日志集 其内的日志文件也一并被删除 但无需额外设置 因为在定义模型时有定义联级删除
@view.route('/deleteset', methods=['GET','POST'])
def deleteset():
    if request.method == 'POST':
       # 通过日记集的id来删除某个日志集 并返回删除后的所有日志集
       plan_id = request.json['plan_id']
       index_set = Logset.query.filter_by(id = plan_id).first()
       db.session.delete(index_set)
       db.session.commit()
       details = searchsets(session['uid'])
       return jsonify({'details':details}),200
    else:
        pass

# 初始化 创建日志 以及 添加关注
# 进入展示某个集合内容的页面
@view.route('/showcontent', methods=['GET','POST'])
def showcontent():
    if request.method == 'GET':
    # 当传值方法为get时 表示用户从某个日志集点击进入详情 需获取到对应日志集的id
       set_id = request.args['id']
       session['set_id'] = set_id
       session.modified = True
       return render_template('base_template/showlogs.html')
    else:
        # 当传值方法为post时 表示前端需要从后端获取数据来初始化页面
        details = searchlogs(session['set_id'])

        return jsonify({'details':details,'uid':session['uid']}),200

# 创建日志的函数
@view.route('/createlog', methods=['GET','POST'])
def createlog():
    if request.method == 'POST':
        title = request.form['name']
        content = request.form['content']
        # 获取前端传输的文件需要使用files
        files = request.files.getlist('file')
        # 存储文字内容
        filename = str(datetime.now().date()) + '_' + title+'.txt'
        f = open(DevelopmentConfig.USER_DIR+'/'+str(session['uid'])+'/text/'+filename,'w')
        f.write(content)
        f.close()
        # 存储图片内容
        img_names = []
        if files:
            for file in files:
                img_name = file.filename
                img_name = secure_filename(img_name)
                img_names.append(img_name)
                file.save(DevelopmentConfig.STATIC_DIR+'/uploads/'+str(session['uid'])+'/'+img_name)
        # 创建log对象
        newlog = Log(title,filename,session['set_id'])
        db.session.add(newlog)
        db.session.commit()
        # 查询到最新的log对象 获取其id
        logs = Log.query.filter_by(set_id=session['set_id']).all()
        newlog = logs[len(logs)-1]
        log_id = newlog.id
        # 存储图片对象
        for i in range(len(img_names)):
            img = Logimages(img_names[i],log_id)
            db.session.add(img)
            db.session.commit()

        return redirect(url_for('view_u.showcontent',id=session['set_id']))
    else:
        pass

# 通过log_id 来设置日志的关注状态
@view.route('/setfocus',methods=['POST','GET'])
def setfocus():
    if request.method == 'POST':
        id = request.json['log_id']
        log = Log.query.filter_by(id=id).first()
        if log.focus:
            log.focus = False
        else:
            log.focus = True
        db.session.commit()
        details = searchlogs(session['set_id'])
        count = 0
        for detail in details:
            if id == detail['id']:
                break
            else:
                count = count+1
        return jsonify({'details':details,'index':count}),200
    else:
        pass





