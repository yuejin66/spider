from peewee import *

db = MySQLDatabase("spider", host="127.0.0.1", port=3306, user="root", password="123456")


class BaseModel(Model):
    class Meta:
        database = db


class Topic(BaseModel):
    id = IntegerField(primary_key=True)
    author = CharField()
    title = CharField()
    create_time = DateTimeField()
    content = TextField(default="")
    answer_nums = IntegerField(default=0)  # 排名数
    click_nums = IntegerField(default=0)
    praised_nums = IntegerField(default=0)  # 点赞数
    jtl = FloatField(default=0.0)  # 结帖率
    score = IntegerField(default=0)  # 赏分
    status = CharField()  # 状态
    last_answer_time = DateTimeField()  # 最后的回复时间


class Answer(BaseModel):
    topic_id = IntegerField()  # 标题id
    author = CharField()
    create_time = DateTimeField()
    content = TextField(default="")
    praised_nums = IntegerField(default=0)


class Author(BaseModel):
    id = CharField(primary_key=True)
    name = CharField(max_length=10)
    original_nums = CharField(max_length=10)  # 原创数
    weeks_rankings_nums = CharField(max_length=10)  # 周排名数
    total_rankings_nums = CharField(max_length=10)  # 总排名数
    PV_nums = CharField(max_length=10)  # 访问量
    integral_nums = CharField(max_length=10)  # 积分数
    follower_nums = CharField(max_length=10)  # 粉丝数
    praised_nums = CharField(max_length=10)  # 获赞数
    comment_nums = CharField(max_length=10)  # 评论数
    collect_nums = CharField(max_length=10)  # 收藏数
    industry = CharField(default="")
    location = CharField(default="")


if __name__ == "__main__":
    db.create_tables([Topic, Answer, Author])
