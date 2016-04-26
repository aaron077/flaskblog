import hashlib
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin
from . import db, login_manager

class BlogInfo(db.Model):
	__tablename__ = 'blog_info'
	id = db.Column(db.Integer,primary_key=True)
	title = db.Column(db.String(64))
	signature = db.Column(db.Text)
	navbar = db.Column(db.String(64))
	
	@staticmethod
	def insert_blog_info():
		blog_mini_info = BlogInfo(title="博客",
			signature="拥有可管理的个人博客",
			navbar='inverse')
		db.session.add(blog_mini_info)
		db.session.commit()

class Menu(db.Model):
	__tablename__="menus"
	id = db.Column(db.Integer,primary_key=True)
	name = db.Column(db.String(64),unique=True)
	types = db.relationship('ArticleType',backref='menu',lazy='dynamic')
	order = db.Column(db.Integer,default=0,nullable=False)

	def sort_delete(self):
		for menu in Menu.query.order_by(Menu.order).offset(self.order).all():
			menu.order -= 1
			db.session.add(menu)
	@staticmethod
	def insert_menus():
		menus = [u'Web开发', u'数据库', u'网络技术', u'爱生活，爱自己',
                 u'Linux世界', u'开发语言']
		for name in menus:
			menu = Menu(name=name)
			db.session.add(menu)
			db.session.commit()
			menu.order = menu.id
			db.session.add(menu)
			db.session.commit()
	@staticmethod
	def return_menus():
		menus = [(m.id,m.name) for m in Menu.query.all()]
		menus.append((-1, u'不选择导航（该分类将单独成一导航）'))
		return menus

	def __repr__(self):
		return '<Menu %r>' % self.name

class ArticleTypeSetting(db.Model):
    __tablename__ = 'articleTypeSettings'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    protected = db.Column(db.Boolean, default=False)
    hide = db.Column(db.Boolean, default=False)
    types = db.relationship('ArticleType', backref='setting', lazy='dynamic')


    @staticmethod
    def insert_system_setting():
        system = ArticleTypeSetting(name='system', protected=True, hide=True)
        db.session.add(system)
        db.session.commit()

    @staticmethod
    def insert_default_settings():
        system_setting = ArticleTypeSetting(name='system', protected=True, hide=True)
        common_setting = ArticleTypeSetting(name='common', protected=False, hide=False)
        db.session.add(system_setting)
        db.session.add(common_setting)
        db.session.commit()

    @staticmethod
    def return_setting_hide():
        return [(2, u'公开'), (1, u'隐藏')]

    def __repr__(self):
        return '<ArticleTypeSetting %r>' % self.name

class ArticleType(db.Model):
    __tablename__ = 'articleTypes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    introduction = db.Column(db.Text, default=None)
    articles = db.relationship('Article', backref='articleType', lazy='dynamic')
    menu_id = db.Column(db.Integer, db.ForeignKey('menus.id'), default=None)
    setting_id = db.Column(db.Integer, db.ForeignKey('articleTypeSettings.id'))


    @staticmethod
    def insert_system_articleType():
        articleType = ArticleType(name=u'未分类',
                                  introduction=u'系统默认分类，不可删除。',
                                  setting=ArticleTypeSetting.query.filter_by(protected=True).first()
                                  )
        db.session.add(articleType)
        db.session.commit()

    @staticmethod
    def insert_articleTypes():
        articleTypes = {u'6': ['Python', 'Java', 'JavaScript'],
                 '5': [u'Linux成长之路', u'Linux运维实战', 'CentOS', 'Ubuntu'],
                 u'3': [u'思科网络技术', u'其它'],
                 u'2': ['MySQL', 'Redis'],
                 u'4': [u'生活那些事', u'学校那些事',u'感情那些事'],
                 u'1': ['Flask', 'Django'],}
        for menuid,types in articleTypes.items():
            for name in types:
                articleType = ArticleType(name=name,menu_id=menuid,setting=ArticleTypeSetting(name=name))
                db.session.add(articleType)
                db.session.commit()


    @property
    def is_protected(self):
        if self.setting:
            return self.setting.protected
        else:
            return False

    @property
    def is_hide(self):
        if self.setting:
            return self.setting.hide
        else:
            return False
    # if the articleType does not have setting,
    # its is_hie and is_protected property will be False.

    def __repr__(self):
        return '<Type %r>' % self.name

class Source(db.Model):
    __tablename__ = 'sources'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    articles = db.relationship('Article', backref='source', lazy='dynamic')

    @staticmethod
    def insert_sources():
        sources = (u'原创',
                   u'转载',
                   u'翻译')
        for s in sources:
            source = Source.query.filter_by(name=s).first()
            if source is None:
                source = Source(name=s)
            db.session.add(source)
        db.session.commit()

    def __repr__(self):
        return '<Source %r>' % self.name
        		
class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), unique=True)
    content = db.Column(db.Text)
    summary = db.Column(db.Text)
    create_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    num_of_view = db.Column(db.Integer, default=0)
    articleType_id = db.Column(db.Integer, db.ForeignKey('articleTypes.id'))
    source_id = db.Column(db.Integer, db.ForeignKey('sources.id'))
  #  comments = db.relationship('Comment', backref='article', lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint
        import forgery_py

        seed()
        articleType_count = ArticleType.query.count()
        source_count = Source.query.count()
        for i in range(count):
            aT = ArticleType.query.offset(randint(0, articleType_count - 1)).first()
            s = Source.query.offset(randint(0, source_count - 1)).first()
            a = Article(title=forgery_py.lorem_ipsum.title(randint(3, 5)),
                        content=forgery_py.lorem_ipsum.sentences(randint(15, 35)),
                        summary=forgery_py.lorem_ipsum.sentences(randint(2, 5)),
                        num_of_view=randint(100, 15000),
                        articleType=aT, source=s)
            db.session.add(a)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    @staticmethod
    def add_view(article, db):
        article.num_of_view += 1
        db.session.add(article)
        db.session.commit()

    def __repr__(self):
        return '<Article %r>' % self.title


